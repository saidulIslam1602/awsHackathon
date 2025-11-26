"""
SQLite Database Manager for Privacy Policy Analyzer
Stores analysis history, cached results, and usage statistics
"""

import sqlite3
import json
import datetime
from pathlib import Path
from typing import Dict, List, Optional

class DatabaseManager:
    """Manages SQLite database for privacy policy analysis data"""
    
    def __init__(self, db_path: str = "privacy_analyzer.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Analysis history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analysis_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    website TEXT NOT NULL,
                    company_name TEXT,
                    analysis_type TEXT,
                    risk_score INTEGER,
                    harmful_points TEXT,
                    worst_data TEXT,
                    recommendation TEXT,
                    privacy_url TEXT,
                    source TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    user_session TEXT
                )
            ''')
            
            # Platform statistics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS platform_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform_name TEXT UNIQUE,
                    analysis_count INTEGER DEFAULT 0,
                    avg_risk_score REAL,
                    last_analyzed DATETIME,
                    total_users INTEGER DEFAULT 0
                )
            ''')
            
            # Cached analysis results
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analysis_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    website TEXT UNIQUE,
                    company_name TEXT,
                    cached_analysis TEXT,
                    cache_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME
                )
            ''')
            
            # User sessions (for analytics)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    session_id TEXT PRIMARY KEY,
                    first_visit DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                    total_analyses INTEGER DEFAULT 0,
                    platforms_analyzed TEXT
                )
            ''')
            
            conn.commit()
            print("✅ Database initialized successfully")
    
    def save_analysis(self, analysis_data: Dict, session_id: str = None) -> int:
        """Save analysis result to database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO analysis_history 
                (website, company_name, analysis_type, risk_score, harmful_points, 
                 worst_data, recommendation, privacy_url, source, user_session)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                analysis_data.get('website', ''),
                analysis_data.get('company_name', ''),
                analysis_data.get('analysis_type', 'unknown'),
                analysis_data.get('score', 0),
                analysis_data.get('harmful_points', ''),
                analysis_data.get('worst_data', ''),
                analysis_data.get('recommendation', ''),
                analysis_data.get('privacy_url', ''),
                analysis_data.get('source', 'unknown'),
                session_id
            ))
            
            analysis_id = cursor.lastrowid
            conn.commit()
            
            # Update platform statistics
            self.update_platform_stats(analysis_data.get('company_name', ''), 
                                     analysis_data.get('score', 0))
            
            return analysis_id
    
    def update_platform_stats(self, platform_name: str, risk_score: int):
        """Update platform analysis statistics"""
        if not platform_name:
            return
            
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if platform exists
            cursor.execute('SELECT * FROM platform_stats WHERE platform_name = ?', (platform_name,))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing record
                new_count = existing[2] + 1
                new_avg = ((existing[3] * existing[2]) + risk_score) / new_count
                
                cursor.execute('''
                    UPDATE platform_stats 
                    SET analysis_count = ?, avg_risk_score = ?, last_analyzed = CURRENT_TIMESTAMP
                    WHERE platform_name = ?
                ''', (new_count, new_avg, platform_name))
            else:
                # Insert new record
                cursor.execute('''
                    INSERT INTO platform_stats (platform_name, analysis_count, avg_risk_score, last_analyzed)
                    VALUES (?, 1, ?, CURRENT_TIMESTAMP)
                ''', (platform_name, risk_score))
            
            conn.commit()
    
    def get_analysis_history(self, limit: int = 50) -> List[Dict]:
        """Get recent analysis history"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT website, company_name, risk_score, source, timestamp
                FROM analysis_history 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
            
            results = cursor.fetchall()
            
            return [
                {
                    'website': row[0],
                    'company_name': row[1],
                    'risk_score': row[2],
                    'source': row[3],
                    'timestamp': row[4]
                }
                for row in results
            ]
    
    def get_platform_stats(self) -> List[Dict]:
        """Get platform analysis statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT platform_name, analysis_count, avg_risk_score, last_analyzed
                FROM platform_stats 
                ORDER BY analysis_count DESC
            ''')
            
            results = cursor.fetchall()
            
            return [
                {
                    'platform': row[0],
                    'analyses': row[1],
                    'avg_risk': round(row[2], 1) if row[2] else 0,
                    'last_analyzed': row[3]
                }
                for row in results
            ]
    
    def cache_analysis(self, website: str, analysis: Dict, expires_hours: int = 24):
        """Cache analysis result for faster future lookups"""
        expires_at = datetime.datetime.now() + datetime.timedelta(hours=expires_hours)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO analysis_cache 
                (website, company_name, cached_analysis, expires_at)
                VALUES (?, ?, ?, ?)
            ''', (
                website,
                analysis.get('company_name', ''),
                json.dumps(analysis),
                expires_at
            ))
            
            conn.commit()
    
    def get_cached_analysis(self, website: str) -> Optional[Dict]:
        """Get cached analysis if available and not expired"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT cached_analysis FROM analysis_cache 
                WHERE website = ? AND expires_at > CURRENT_TIMESTAMP
            ''', (website,))
            
            result = cursor.fetchone()
            
            if result:
                return json.loads(result[0])
            
            return None
    
    def update_user_session(self, session_id: str, platform_analyzed: str = None):
        """Update user session statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if session exists
            cursor.execute('SELECT * FROM user_sessions WHERE session_id = ?', (session_id,))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing session
                total_analyses = existing[3] + 1
                platforms = existing[4].split(',') if existing[4] else []
                
                if platform_analyzed and platform_analyzed not in platforms:
                    platforms.append(platform_analyzed)
                
                cursor.execute('''
                    UPDATE user_sessions 
                    SET last_activity = CURRENT_TIMESTAMP, total_analyses = ?, platforms_analyzed = ?
                    WHERE session_id = ?
                ''', (total_analyses, ','.join(platforms), session_id))
            else:
                # Create new session
                platforms = [platform_analyzed] if platform_analyzed else []
                cursor.execute('''
                    INSERT INTO user_sessions (session_id, total_analyses, platforms_analyzed)
                    VALUES (?, 1, ?)
                ''', (session_id, ','.join(platforms)))
            
            conn.commit()
    
    def get_dashboard_stats(self) -> Dict:
        """Get statistics for admin dashboard"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total analyses
            cursor.execute('SELECT COUNT(*) FROM analysis_history')
            total_analyses = cursor.fetchone()[0]
            
            # Unique websites analyzed
            cursor.execute('SELECT COUNT(DISTINCT website) FROM analysis_history')
            unique_websites = cursor.fetchone()[0]
            
            # Average risk score
            cursor.execute('SELECT AVG(risk_score) FROM analysis_history WHERE risk_score > 0')
            avg_risk = cursor.fetchone()[0] or 0
            
            # Analyses today
            cursor.execute('''
                SELECT COUNT(*) FROM analysis_history 
                WHERE DATE(timestamp) = DATE('now')
            ''')
            analyses_today = cursor.fetchone()[0]
            
            # Most analyzed platforms
            cursor.execute('''
                SELECT company_name, COUNT(*) as count 
                FROM analysis_history 
                WHERE company_name IS NOT NULL 
                GROUP BY company_name 
                ORDER BY count DESC 
                LIMIT 5
            ''')
            top_platforms = cursor.fetchall()
            
            return {
                'total_analyses': total_analyses,
                'unique_websites': unique_websites,
                'avg_risk_score': round(avg_risk, 1),
                'analyses_today': analyses_today,
                'top_platforms': [{'name': p[0], 'count': p[1]} for p in top_platforms]
            }
    
    def cleanup_expired_cache(self):
        """Remove expired cache entries"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM analysis_cache WHERE expires_at < CURRENT_TIMESTAMP')
            deleted = cursor.rowcount
            conn.commit()
            
            return deleted

# Global database instance
db = DatabaseManager()
