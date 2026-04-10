use crate::db::BibleDb;
use crate::error::BibleError;
use crate::models::{Book, Translation, Verse};

impl BibleDb {
    /// Look up a verse by its database primary key (verses.id).
    pub fn get_verse_by_id(&self, id: i64) -> Result<Option<Verse>, BibleError> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare(
            "SELECT id, translation_id, book_number, book_name, book_abbreviation, chapter, verse, text \
             FROM verses WHERE id = ?1",
        )?;
        let mut rows = stmt.query_map(rusqlite::params![id], |row: &rusqlite::Row| {
            Ok(Verse {
                id: row.get(0)?,
                translation_id: row.get(1)?,
                book_number: row.get(2)?,
                book_name: row.get(3)?,
                book_abbreviation: row.get(4)?,
                chapter: row.get(5)?,
                verse: row.get(6)?,
                text: row.get(7)?,
            })
        })?;
        match rows.next() {
            Some(row) => Ok(Some(row?)),
            None => Ok(None),
        }
    }

    pub fn get_verse(
        &self,
        translation_id: i64,
        book_number: i32,
        chapter: i32,
        verse: i32,
    ) -> Result<Option<Verse>, BibleError> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare(
            "SELECT id, translation_id, book_number, book_name, book_abbreviation, chapter, verse, text \
             FROM verses \
             WHERE translation_id = ?1 AND book_number = ?2 AND chapter = ?3 AND verse = ?4",
        )?;
        let mut rows = stmt.query_map(
            rusqlite::params![translation_id, book_number, chapter, verse],
            |row: &rusqlite::Row| {
                Ok(Verse {
                    id: row.get(0)?,
                    translation_id: row.get(1)?,
                    book_number: row.get(2)?,
                    book_name: row.get(3)?,
                    book_abbreviation: row.get(4)?,
                    chapter: row.get(5)?,
                    verse: row.get(6)?,
                    text: row.get(7)?,
                })
            },
        )?;
        match rows.next() {
            Some(row) => Ok(Some(row?)),
            None => Ok(None),
        }
    }

    pub fn get_chapter(
        &self,
        translation_id: i64,
        book_number: i32,
        chapter: i32,
    ) -> Result<Vec<Verse>, BibleError> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare(
            "SELECT id, translation_id, book_number, book_name, book_abbreviation, chapter, verse, text \
             FROM verses \
             WHERE translation_id = ?1 AND book_number = ?2 AND chapter = ?3 \
             ORDER BY verse",
        )?;
        let rows = stmt.query_map(
            rusqlite::params![translation_id, book_number, chapter],
            |row: &rusqlite::Row| {
                Ok(Verse {
                    id: row.get(0)?,
                    translation_id: row.get(1)?,
                    book_number: row.get(2)?,
                    book_name: row.get(3)?,
                    book_abbreviation: row.get(4)?,
                    chapter: row.get(5)?,
                    verse: row.get(6)?,
                    text: row.get(7)?,
                })
            },
        )?;
        let mut verses = Vec::new();
        for row in rows {
            verses.push(row?);
        }
        Ok(verses)
    }

    pub fn get_verse_range(
        &self,
        translation_id: i64,
        book_number: i32,
        chapter: i32,
        verse_start: i32,
        verse_end: i32,
    ) -> Result<Vec<Verse>, BibleError> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare(
            "SELECT id, translation_id, book_number, book_name, book_abbreviation, chapter, verse, text \
             FROM verses \
             WHERE translation_id = ?1 AND book_number = ?2 AND chapter = ?3 \
               AND verse >= ?4 AND verse <= ?5 \
             ORDER BY verse",
        )?;
        let rows = stmt.query_map(
            rusqlite::params![translation_id, book_number, chapter, verse_start, verse_end],
            |row: &rusqlite::Row| {
                Ok(Verse {
                    id: row.get(0)?,
                    translation_id: row.get(1)?,
                    book_number: row.get(2)?,
                    book_name: row.get(3)?,
                    book_abbreviation: row.get(4)?,
                    chapter: row.get(5)?,
                    verse: row.get(6)?,
                    text: row.get(7)?,
                })
            },
        )?;
        let mut verses = Vec::new();
        for row in rows {
            verses.push(row?);
        }
        Ok(verses)
    }

    /// Load all verses for quotation matching index.
    /// Returns (id, book_number, book_name, chapter, verse, text) tuples.
    /// Filters to a specific language if provided.
    /// Load all verses for quotation matching index.
    /// Returns (id, book_number, book_name, chapter, verse, text) tuples.
    /// Filters to a specific language if provided.
    pub fn load_all_verses_for_quotation(
        &self,
        language: Option<&str>,
    ) -> Result<Vec<(i64, i32, String, i32, i32, String)>, BibleError> {
        let conn = self.conn.lock().unwrap();

        let mapper = |row: &rusqlite::Row| {
            Ok((
                row.get::<_, i64>(0)?,
                row.get::<_, i32>(1)?,
                row.get::<_, String>(2)?,
                row.get::<_, i32>(3)?,
                row.get::<_, i32>(4)?,
                row.get::<_, String>(5)?,
            ))
        };

        let mut results = Vec::new();

        if let Some(lang) = language {
            let mut stmt = conn.prepare(
                "SELECT v.id, v.book_number, v.book_name, v.chapter, v.verse, v.text \
                 FROM verses v \
                 JOIN translations t ON v.translation_id = t.id \
                 WHERE t.language = ?1"
            )?;
            let rows = stmt.query_map([lang], mapper)?;
            for row in rows {
                results.push(row?);
            }
        } else {
            let mut stmt = conn.prepare(
                "SELECT id, book_number, book_name, chapter, verse, text FROM verses"
            )?;
            let rows = stmt.query_map([], mapper)?;
            for row in rows {
                results.push(row?);
            }
        }

        Ok(results)
    }

    /// Load all verses for one translation for client-side context search indexing.
    /// Returns compact tuples: (book_number, book_name, chapter, verse, text).
    pub fn load_translation_verses_for_search(
        &self,
        translation_id: i64,
    ) -> Result<Vec<(i32, String, i32, i32, String)>, BibleError> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare(
            "SELECT book_number, book_name, chapter, verse, text \
             FROM verses \
             WHERE translation_id = ?1 \
             ORDER BY book_number, chapter, verse",
        )?;
        let rows = stmt.query_map([translation_id], |row: &rusqlite::Row| {
            Ok((
                row.get::<_, i32>(0)?,
                row.get::<_, String>(1)?,
                row.get::<_, i32>(2)?,
                row.get::<_, i32>(3)?,
                row.get::<_, String>(4)?,
            ))
        })?;

        let mut results = Vec::new();
        for row in rows {
            results.push(row?);
        }
        Ok(results)
    }

    pub fn list_translations(&self) -> Result<Vec<Translation>, BibleError> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare(
            "SELECT id, abbreviation, title, language, is_copyrighted, is_downloaded \
             FROM translations",
        )?;
        let rows = stmt.query_map([], |row: &rusqlite::Row| {
            Ok(Translation {
                id: row.get(0)?,
                abbreviation: row.get(1)?,
                title: row.get(2)?,
                language: row.get(3)?,
                is_copyrighted: row.get(4)?,
                is_downloaded: row.get(5)?,
            })
        })?;
        let mut translations = Vec::new();
        for row in rows {
            translations.push(row?);
        }
        Ok(translations)
    }

    pub fn list_books(&self, translation_id: i64) -> Result<Vec<Book>, BibleError> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare(
            "SELECT id, translation_id, book_number, name, abbreviation, testament \
             FROM books \
             WHERE translation_id = ?1 \
             ORDER BY book_number",
        )?;
        let rows = stmt.query_map(rusqlite::params![translation_id], |row: &rusqlite::Row| {
            Ok(Book {
                id: row.get(0)?,
                translation_id: row.get(1)?,
                book_number: row.get(2)?,
                name: row.get(3)?,
                abbreviation: row.get(4)?,
                testament: row.get(5)?,
            })
        })?;
        let mut books = Vec::new();
        for row in rows {
            books.push(row?);
        }
        Ok(books)
    }
}
