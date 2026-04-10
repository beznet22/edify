use crate::types::AudioLevel;

const I16_MAX: f32 = i16::MAX as f32;

/// Compute the RMS and peak level from a slice of i16 samples.
/// Both values are normalized to the range 0.0..=1.0.
pub fn compute_level(samples: &[i16]) -> AudioLevel {
    if samples.is_empty() {
        return AudioLevel { rms: 0.0, peak: 0.0 };
    }

    let mut sum_sq: f64 = 0.0;
    let mut peak_abs: i16 = 0;

    for &s in samples {
        sum_sq += (s as f64) * (s as f64);
        let abs = s.saturating_abs();
        if abs > peak_abs {
            peak_abs = abs;
        }
    }

    let rms = ((sum_sq / samples.len() as f64).sqrt() as f32) / I16_MAX;
    let peak = peak_abs as f32 / I16_MAX;

    AudioLevel {
        rms: rms.clamp(0.0, 1.0),
        peak: peak.clamp(0.0, 1.0),
    }
}
