"""WebSocket handlers for real-time test streaming"""
import asyncio
import json
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict

import aiohttp
from quart import websocket, current_app, request
import jwt

logger = logging.getLogger(__name__)


@dataclass
class StreamMessage:
    """WebSocket message structure"""
    event: str
    data: Dict[str, Any]

    def to_json(self) -> str:
        """Serialize message to JSON"""
        return json.dumps(asdict(self))


async def validate_websocket_session(session_id: str) -> Optional[int]:  # pragma: no cover
    """Authenticate WebSocket connection using session_id.

    Args:
        session_id: Session identifier from WebSocket query parameter

    Returns:
        user_id if valid, None otherwise
    """
    if not session_id:
        logger.warning("WebSocket connection attempted without session_id")
        return None

    try:
        # Extract JWT from session_id or get from Authorization header
        auth_header = request.headers.get('Authorization', '')
        token = None

        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
        elif session_id.startswith('Bearer '):
            token = session_id[7:]
        else:
            token = session_id

        if not token:
            logger.warning("No valid token found in WebSocket connection")
            return None

        payload = jwt.decode(
            token,
            current_app.config['JWT_SECRET'],
            algorithms=['HS256']
        )

        user_id = payload.get('user_id')
        if not user_id:
            logger.warning("Token missing user_id claim")
            return None

        logger.info(f"WebSocket session validated for user {user_id}")
        return user_id

    except jwt.ExpiredSignatureError:
        logger.warning("WebSocket token has expired")
        return None
    except (jwt.InvalidTokenError, jwt.DecodeError) as e:
        logger.warning(f"Invalid WebSocket token: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error validating WebSocket session: {str(e)}")
        return None


async def execute_test_with_streaming(  # pragma: no cover
    test_params: Dict[str, Any]
) -> Optional[asyncio.StreamReader]:
    """Call testServer API with aiohttp and return response stream.

    Args:
        test_params: Test execution parameters

    Returns:
        Response stream reader or None on error
    """
    try:
        testserver_url = current_app.config.get(
            'TESTSERVER_URL',
            'http://testserver:8080'
        )
        api_url = f"{testserver_url}/api/v1/tests/execute"

        logger.info(f"Executing test via {api_url}")

        timeout = aiohttp.ClientTimeout(total=3600)  # 1 hour timeout
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                api_url,
                json=test_params,
                ssl=False  # For development, disable SSL verification
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    logger.error(
                        f"testServer returned {resp.status}: {error_text}"
                    )
                    return None

                # Return the response for streaming
                return resp

    except asyncio.TimeoutError:
        logger.error("testServer request timeout")
        return None
    except aiohttp.ClientError as e:
        logger.error(f"HTTP client error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error executing test: {str(e)}")
        return None


async def stream_test_progress(  # pragma: no cover
    response: aiohttp.ClientResponse,
    ws
) -> None:
    """Stream test progress updates from testServer to WebSocket client.

    Args:
        response: aiohttp response object
        ws: WebSocket connection object
    """
    try:
        async for line in response.content:
            if not line:
                continue

            try:
                # Assume testServer sends newline-delimited JSON
                line_str = line.decode('utf-8').strip()
                if not line_str:
                    continue

                event_data = json.loads(line_str)

                # Forward test_progress events
                if event_data.get('event') == 'progress':
                    msg = StreamMessage(
                        event='test_progress',
                        data={
                            'timestamp': event_data.get('timestamp'),
                            'progress_percent': event_data.get('progress_percent'),
                            'current_step': event_data.get('current_step'),
                            'message': event_data.get('message'),
                            'metrics': event_data.get('metrics', {}),
                        }
                    )
                    await ws.send(msg.to_json())

                # Forward test completion
                elif event_data.get('event') == 'complete':
                    msg = StreamMessage(
                        event='test_complete',
                        data={
                            'test_id': event_data.get('test_id'),
                            'status': event_data.get('status'),
                            'duration_ms': event_data.get('duration_ms'),
                            'success': event_data.get('success'),
                            'results': event_data.get('results', {}),
                            'error_message': event_data.get('error_message'),
                        }
                    )
                    await ws.send(msg.to_json())
                    break  # Test completed, exit streaming loop

            except json.JSONDecodeError as e:
                logger.warning(f"Failed to decode JSON from testServer: {str(e)}")
                continue
            except Exception as e:
                logger.warning(f"Error processing test progress: {str(e)}")
                continue

    except asyncio.CancelledError:
        logger.info("Test streaming cancelled by client")
    except Exception as e:
        logger.error(f"Error streaming test progress: {str(e)}")
        msg = StreamMessage(
            event='error',
            data={'message': f'Streaming error: {str(e)}'}
        )
        await ws.send(msg.to_json())


async def handle_test_execution() -> None:  # pragma: no cover
    """Main WebSocket handler for test execution.

    Accepts WebSocket connections and manages real-time test streaming.
    Expected message format:
        {
            "event": "start_test",
            "data": {
                "test_name": "test_name",
                "device_id": 1,
                "organization_id": 1,
                "parameters": {...}
            }
        }
    """
    ws = websocket.server
    session_id = request.args.get('session_id', '')

    # Validate WebSocket session
    user_id = await validate_websocket_session(session_id)
    if not user_id:
        logger.warning("WebSocket authentication failed, closing connection")
        await ws.close(code=1008, message='Unauthorized')
        return

    logger.info(f"WebSocket connection established for user {user_id}")

    test_task = None
    try:
        async for message in ws.receive():
            try:
                msg_data = json.loads(message)
                event = msg_data.get('event')

                if event == 'start_test':
                    # Cancel previous test if running
                    if test_task and not test_task.done():
                        test_task.cancel()
                        logger.info("Cancelled previous test task")

                    # Extract test parameters
                    params = msg_data.get('data', {})
                    logger.info(f"Received start_test event with params: {params}")

                    # Start test execution task
                    test_task = asyncio.create_task(
                        _run_test_stream(ws, params)
                    )

                elif event == 'cancel_test':
                    # Cancel running test
                    if test_task and not test_task.done():
                        test_task.cancel()
                        msg = StreamMessage(
                            event='test_cancelled',
                            data={'message': 'Test execution cancelled'}
                        )
                        await ws.send(msg.to_json())
                        logger.info("Test execution cancelled")

                elif event == 'ping':
                    # Respond to ping to keep connection alive
                    msg = StreamMessage(event='pong', data={})
                    await ws.send(msg.to_json())

            except json.JSONDecodeError:
                logger.warning("Received invalid JSON from client")
                msg = StreamMessage(
                    event='error',
                    data={'message': 'Invalid JSON format'}
                )
                await ws.send(msg.to_json())

    except asyncio.CancelledError:
        logger.info(f"WebSocket handler cancelled for user {user_id}")
        if test_task and not test_task.done():
            test_task.cancel()
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        try:
            msg = StreamMessage(
                event='error',
                data={'message': f'WebSocket error: {str(e)}'}
            )
            await ws.send(msg.to_json())
        except Exception:
            pass  # Connection may be closed
    finally:
        logger.info(f"WebSocket connection closed for user {user_id}")
        if test_task and not test_task.done():
            test_task.cancel()


async def _run_test_stream(ws, params: Dict[str, Any]) -> None:  # pragma: no cover
    """Internal function to run test and stream progress.

    Args:
        ws: WebSocket connection
        params: Test parameters
    """
    try:
        # Validate required parameters
        if not params.get('test_name'):
            msg = StreamMessage(
                event='error',
                data={'message': 'Missing required parameter: test_name'}
            )
            await ws.send(msg.to_json())
            return

        # Send test_started event
        msg = StreamMessage(
            event='test_started',
            data={
                'test_name': params.get('test_name'),
                'message': 'Test execution started'
            }
        )
        await ws.send(msg.to_json())

        # Execute test with testServer
        response = await execute_test_with_streaming(params)
        if not response:
            msg = StreamMessage(
                event='error',
                data={'message': 'Failed to connect to testServer'}
            )
            await ws.send(msg.to_json())
            return

        # Stream progress updates
        await stream_test_progress(response, ws)

    except asyncio.CancelledError:
        logger.info("Test stream task cancelled")
    except Exception as e:
        logger.error(f"Error in test stream: {str(e)}")
        msg = StreamMessage(
            event='error',
            data={'message': f'Test execution error: {str(e)}'}
        )
        try:
            await ws.send(msg.to_json())
        except Exception:
            pass
