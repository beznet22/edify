use thiserror::Error;

#[derive(Error, Debug)]
pub enum DetectionError {
    #[error("Failed to parse reference: {0}")]
    ParseError(String),

    #[error("Invalid book name: {0}")]
    InvalidBook(String),

    #[error("Invalid chapter or verse number: {0}")]
    InvalidNumber(String),

    #[error("Internal error: {0}")]
    Internal(String),
}
