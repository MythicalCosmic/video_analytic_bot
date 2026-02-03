"""
High-performance JSON data importer

Uses asyncpg's COPY protocol for maximum insert speed.
Imports 358 videos + 35,946 snapshots in seconds.

Usage:
    python -m scripts.import_data path/to/videos.json
"""
import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

import asyncpg

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import settings


async def create_tables(conn: asyncpg.Connection):
    await conn.execute("DROP TABLE IF EXISTS video_snapshots CASCADE")
    await conn.execute("DROP TABLE IF EXISTS videos CASCADE")

    await conn.execute("""
        CREATE TABLE videos (
            id VARCHAR(36) PRIMARY KEY,
            creator_id VARCHAR(32) NOT NULL,
            video_created_at TIMESTAMPTZ NOT NULL,
            views_count INTEGER DEFAULT 0,
            likes_count INTEGER DEFAULT 0,
            comments_count INTEGER DEFAULT 0,
            reports_count INTEGER DEFAULT 0,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    await conn.execute("""
        CREATE TABLE video_snapshots (
            id VARCHAR(32) PRIMARY KEY,
            video_id VARCHAR(36) NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
            views_count INTEGER DEFAULT 0,
            likes_count INTEGER DEFAULT 0,
            comments_count INTEGER DEFAULT 0,
            reports_count INTEGER DEFAULT 0,
            delta_views_count INTEGER DEFAULT 0,
            delta_likes_count INTEGER DEFAULT 0,
            delta_comments_count INTEGER DEFAULT 0,
            delta_reports_count INTEGER DEFAULT 0,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    
    print("Tables created")


async def create_indexes(conn: asyncpg.Connection):
    
    print("Creating indexes...")
    
    await conn.execute("CREATE INDEX idx_videos_creator_id ON videos(creator_id)")
    await conn.execute("CREATE INDEX idx_videos_video_created_at ON videos(video_created_at)")
    await conn.execute("CREATE INDEX idx_videos_views_count ON videos(views_count)")
    await conn.execute("CREATE INDEX idx_videos_creator_date ON videos(creator_id, video_created_at)")
    
    await conn.execute("CREATE INDEX idx_snapshots_video_id ON video_snapshots(video_id)")
    await conn.execute("CREATE INDEX idx_snapshots_created_at ON video_snapshots(created_at)")
    await conn.execute("CREATE INDEX idx_snapshots_video_created ON video_snapshots(video_id, created_at)")
    
    await conn.execute("""
        CREATE INDEX idx_snapshots_created_date 
        ON video_snapshots((created_at::date))
    """)
    
    await conn.execute("""
        CREATE INDEX idx_snapshots_delta_positive 
        ON video_snapshots(video_id, created_at) 
        WHERE delta_views_count > 0
    """)
    
    print("Indexes created")


def parse_datetime(dt_str: str) -> datetime:
    if '.' in dt_str:
        return datetime.fromisoformat(dt_str.replace('+00:00', '+00:00'))
    return datetime.fromisoformat(dt_str)


def prepare_video_record(video: dict) -> Tuple:
    return (
        video['id'],
        video['creator_id'],
        parse_datetime(video['video_created_at']),
        video.get('views_count', 0),
        video.get('likes_count', 0),
        video.get('comments_count', 0),
        video.get('reports_count', 0),
        parse_datetime(video['created_at']),
        parse_datetime(video['updated_at']),
    )


def prepare_snapshot_record(snapshot: dict) -> Tuple:
    return (
        snapshot['id'],
        snapshot['video_id'],
        snapshot.get('views_count', 0),
        snapshot.get('likes_count', 0),
        snapshot.get('comments_count', 0),
        snapshot.get('reports_count', 0),
        snapshot.get('delta_views_count', 0),
        snapshot.get('delta_likes_count', 0),
        snapshot.get('delta_comments_count', 0),
        snapshot.get('delta_reports_count', 0),
        parse_datetime(snapshot['created_at']),
        parse_datetime(snapshot['updated_at']),
    )


async def import_data(json_path: str):
    
    start_time = time.time()
    
    print(f"Loading JSON from: {json_path}")
    
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    videos_data = data['videos']
    print(f"Found {len(videos_data)} videos")
    
    print("Preparing records...")
    
    video_records: List[Tuple] = []
    snapshot_records: List[Tuple] = []
    
    for video in videos_data:
        video_records.append(prepare_video_record(video))
        
        for snapshot in video.get('snapshots', []):
            snapshot_records.append(prepare_snapshot_record(snapshot))
    
    print(f"Prepared {len(video_records)} videos, {len(snapshot_records)} snapshots")
    
    print(f"Connecting to database: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    
    conn = await asyncpg.connect(dsn=settings.asyncpg_dsn)
    
    try:
        await create_tables(conn)
        print("⚡ Inserting videos...")
        await conn.copy_records_to_table(
            'videos',
            records=video_records,
            columns=[
                'id', 'creator_id', 'video_created_at',
                'views_count', 'likes_count', 'comments_count', 'reports_count',
                'created_at', 'updated_at'
            ]
        )
        print(f"Inserted {len(video_records)} videos")
        
        print("⚡ Inserting snapshots...")
        await conn.copy_records_to_table(
            'video_snapshots',
            records=snapshot_records,
            columns=[
                'id', 'video_id',
                'views_count', 'likes_count', 'comments_count', 'reports_count',
                'delta_views_count', 'delta_likes_count', 'delta_comments_count', 'delta_reports_count',
                'created_at', 'updated_at'
            ]
        )
        print(f"Inserted {len(snapshot_records)} snapshots")
        
        await create_indexes(conn)

        print("Running ANALYZE...")
        await conn.execute("ANALYZE videos")
        await conn.execute("ANALYZE video_snapshots")
        
        elapsed = time.time() - start_time
        print(f"\nImport completed in {elapsed:.2f} seconds!")
        print(f"   Videos: {len(video_records)}")
        print(f"   Snapshots: {len(snapshot_records)}")
        print(f"   Speed: {(len(video_records) + len(snapshot_records)) / elapsed:.0f} records/sec")
        
    finally:
        await conn.close()


async def verify_data():
    conn = await asyncpg.connect(dsn=settings.asyncpg_dsn)
    
    try:
        video_count = await conn.fetchval("SELECT COUNT(*) FROM videos")
        snapshot_count = await conn.fetchval("SELECT COUNT(*) FROM video_snapshots")
        creator_count = await conn.fetchval("SELECT COUNT(DISTINCT creator_id) FROM videos")
        
        print(f"\n Data verification:")
        print(f"   Videos: {video_count}")
        print(f"   Snapshots: {snapshot_count}")
        print(f"   Unique creators: {creator_count}")
        
        result = await conn.fetchval("""
            SELECT COALESCE(SUM(delta_views_count), 0) 
            FROM video_snapshots 
            WHERE created_at::date = '2025-11-28'
        """)
        print(f"   Sample query (Nov 28 delta views): {result}")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.import_data <path_to_json>")
        print("Example: python -m scripts.import_data data/videos.json")
        sys.exit(1)
    
    json_path = sys.argv[1]
    
    if not Path(json_path).exists():
        print(f"File not found: {json_path}")
        sys.exit(1)
    
    asyncio.run(import_data(json_path))
    asyncio.run(verify_data())