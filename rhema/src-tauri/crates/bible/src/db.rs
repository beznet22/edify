use std::path::Path;
use std::sync::Mutex;

use rusqlite::Connection;

use crate::error::BibleError;

pub struct BibleDb {
    pub(crate) conn: Mutex<Connection>,
}

impl BibleDb {
    pub fn open(path: &Path) -> Result<Self, BibleError> {
        let conn = Connection::open(path)?;
        conn.execute_batch("PRAGMA journal_mode=WAL;")?;
        Ok(Self {
            conn: Mutex::new(conn),
        })
    }
}
