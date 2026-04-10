use thiserror::Error;

#[derive(Error, Debug)]
pub enum AudioError {
    #[error("Device not found: {0}")]
    DeviceNotFound(String),

    #[error("No input devices available")]
    NoInputDevices,

    #[error("Stream error: {0}")]
    StreamError(String),

    #[error("Channel error: {0}")]
    ChannelError(String),
}
