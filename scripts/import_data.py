import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Tuple
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncpg
from core.config import config


async def create_tables(conn: asyncpg.Connection):
    tables_exist = await conn.fetchval("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'videos'
        )
    """)
    
    if tables_exist:
        print("Tables already exist, skipping creation")
        return False
    
    print("Creating tables...")
    
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
    return True


async def create_indexes(conn: asyncpg.Connection):
    print("Creating indexes...")
    
    await conn.execute("CREATE INDEX idx_videos_creator_id ON videos(creator_id)")
    await conn.execute("CREATE INDEX idx_videos_video_created_at ON videos(video_created_at)")
    await conn.execute("CREATE INDEX idx_videos_views_count ON videos(views_count)")
    await conn.execute("CREATE INDEX idx_videos_creator_date ON videos(creator_id, video_created_at)")
    
    await conn.execute("CREATE INDEX idx_snapshots_video_id ON video_snapshots(video_id)")
    await conn.execute("CREATE INDEX idx_snapshots_created_at ON video_snapshots(created_at)")
    await conn.execute("CREATE INDEX idx_snapshots_video_created ON video_snapshots(video_id, created_at)")
    
    print("Indexes created")


def parse_datetime(dt_str: str) -> datetime:
    return datetime.fromisoformat(dt_str.replace('+00:00', '+00:00'))


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


async def import_data():
    json_path = Path(__file__).parent.parent / "data" / "videos.json"
    
    if not json_path.exists():
        print(f"File not found: {json_path}")
        print("Make sure videos.json is in the 'data' folder!")
        return
    
    start_time = time.time()
    
    dsn = config.asyncpg_dsn
    print(f"Connecting to: {config.db_host}:{config.db_port}/{config.db_name}")
    
    conn = await asyncpg.connect(dsn=dsn)
    
    try:
        tables_created = await create_tables(conn)
        
        if not tables_created:
            existing_count = await conn.fetchval("SELECT COUNT(*) FROM videos")
            if existing_count > 0:
                print(f"Database already has {existing_count} videos. Skipping import.")
                return
        
        print(f"Loading JSON from: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
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
        
        print("Inserting videos...")
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
        
        print("Inserting snapshots...")
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
    dsn = config.asyncpg_dsn
    conn = await asyncpg.connect(dsn=dsn)
    
    try:
        video_count = await conn.fetchval("SELECT COUNT(*) FROM videos")
        snapshot_count = await conn.fetchval("SELECT COUNT(*) FROM video_snapshots")
        creator_count = await conn.fetchval("SELECT COUNT(DISTINCT creator_id) FROM videos")
        
        print(f"\nData verification:")
        print(f"   Videos: {video_count}")
        print(f"   Snapshots: {snapshot_count}")
        print(f"   Unique creators: {creator_count}")
        
        print("\nTesting sample queries...")
        
        result = await conn.fetchval("SELECT COUNT(*) FROM videos")
        print(f"   Total videos: {result}")
        
        result = await conn.fetchval("SELECT COUNT(*) FROM videos WHERE views_count > 100000")
        print(f"   Videos with >100k views: {result}")
        
        result = await conn.fetchval("""
            SELECT COALESCE(SUM(delta_views_count), 0) 
            FROM video_snapshots 
            WHERE created_at::date = '2025-11-28'
        """)
        print(f"   Delta views on Nov 28: {result}")
        
        result = await conn.fetchval("""
            SELECT COUNT(DISTINCT video_id) 
            FROM video_snapshots 
            WHERE created_at::date = '2025-11-27' AND delta_views_count > 0
        """)
        print(f"   Videos with new views on Nov 27: {result}")
        
        print("\nAll queries working!")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    print("=" * 50)
    print("Video Analytics Data Importer")
    print("=" * 50)
    
    asyncio.run(import_data())
    asyncio.run(verify_data())