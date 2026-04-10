pub mod types;
pub mod error;
pub mod direct;
pub mod semantic;
pub mod merger;
pub mod pipeline;
pub mod sentence_buffer;
pub mod reading_mode;
pub mod context;
pub mod quotation;

pub use types::*;
pub use error::*;
pub use direct::detector::DirectDetector;
pub use semantic::detector::SemanticDetector;
pub use semantic::cloud::CloudBooster;
pub use merger::{DetectionMerger, MergedDetection};
pub use pipeline::DetectionPipeline;
pub use sentence_buffer::SentenceBuffer;
pub use reading_mode::{ReadingMode, ReadingAdvance};
pub use context::SermonContext;
pub use quotation::QuotationMatcher;

#[cfg(feature = "onnx")]
pub use semantic::onnx_embedder::OnnxEmbedder;

#[cfg(feature = "vector-search")]
pub use semantic::hnsw_index::HnswVectorIndex;
