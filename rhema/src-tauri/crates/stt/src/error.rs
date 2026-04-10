use thiserror::Error;

#[derive(Error, Debug)]
pub enum SttError {
    #[error("Connection failed: {0}")]
    ConnectionFailed(String),

    #[error("WebSocket error: {0}")]
    WebSocketError(String),

    #[error("API key is missing")]
    ApiKeyMissing,

    #[error("Send error: {0}")]
    SendError(String),

    #[error("Parse error: {0}")]
    ParseError(String),
}
