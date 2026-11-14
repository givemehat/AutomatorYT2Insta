import time
import argparse
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn

from app.config import settings
from app.database import init_db, SessionLocal
from app.models.youtube_video import YouTubeVideo
from app.services.youtube import YouTubeService
from app.services.pipeline import PipelineOrchestrator

console = Console()

def run_migration(
    channel_id: str = None,
    max_videos: int = 40,
    delay_seconds: int = 5,
    reframe_style: str = "smart_face_track"
):
    """
    Safely migrates existing YouTube videos with rate-limiting, progress bars, and duplicate avoidance.
    """
    init_db()
    target_channel = channel_id or settings.YOUTUBE_CHANNEL_ID
    if not target_channel:
        console.print("[bold red]Error: No YouTube Channel ID provided.[/bold red] Pass --channel-id or set YOUTUBE_CHANNEL_ID in .env")
        return

    console.print(f"[bold cyan]🔍 Scanning channel videos:[/bold cyan] [yellow]{target_channel}[/yellow] (Target max: {max_videos})")
    
    videos = YouTubeService.fetch_channel_videos(channel_id=target_channel, max_results=max_videos)
    console.print(f"[bold green]✓ Discovered {len(videos)} videos on channel.[/bold green]\n")

    summary_table = Table(title="Migration Queue")
    summary_table.add_column("No.", style="cyan", width=4)
    summary_table.add_column("Video ID", style="magenta")
    summary_table.add_column("Title", style="white")
    summary_table.add_column("Database Status", style="green")

    with SessionLocal() as db:
        for idx, v in enumerate(videos, 1):
            existing = db.query(YouTubeVideo).filter(YouTubeVideo.youtube_id == v["youtube_id"]).first()
            status_str = existing.processing_status if existing else "NEW (Unprocessed)"
            summary_table.add_row(str(idx), v["youtube_id"], v["title"][:48], status_str)

    console.print(summary_table)
    console.print(f"\n[bold yellow]🚀 Initiating Repurposing Pipeline (Reframe Mode: {reframe_style})...[/bold yellow]\n")

    success_count = 0
    skipped_count = 0
    failed_count = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Processing Videos...", total=len(videos))

        for v in videos:
            v_id = v["youtube_id"]
            progress.update(task, description=f"[yellow]Processing {v_id} - {v['title'][:25]}...")

            with SessionLocal() as db:
                existing = db.query(YouTubeVideo).filter(YouTubeVideo.youtube_id == v_id).first()
                if existing and existing.processing_status in ["PROCESSED", "SKIPPED"]:
                    console.print(f"[dim]• Video {v_id} already finished ({existing.processing_status}). Skipping.[/dim]")
                    skipped_count += 1
                    progress.advance(task)
                    continue

            try:
                res = PipelineOrchestrator.run_full_pipeline_for_video(v_id, reframe_style=reframe_style)
                if res.get("status") == "SKIPPED":
                    console.print(f"[yellow]• Video {v_id} AI Decision: SKIP ({res.get('reason')})[/yellow]")
                    skipped_count += 1
                else:
                    clips_count = len(res.get("clips", []))
                    console.print(f"[green]✓ Video {v_id} repurposed! ({clips_count} 9:16 reels created)[/green]")
                    success_count += 1
            except Exception as e:
                console.print(f"[red]✗ Video {v_id} failed: {e}[/red]")
                failed_count += 1

            progress.advance(task)
            if delay_seconds > 0:
                time.sleep(delay_seconds)

    console.print("\n[bold green]====================================================[/bold green]")
    console.print(f"[bold green] Batch Migration Complete:[/bold green] {success_count} processed, {skipped_count} skipped, {failed_count} failed")
    console.print("[bold green]====================================================[/bold green]")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate existing YouTube videos into Instagram Reels pipeline.")
    parser.add_argument("--channel-id", type=str, help="YouTube Channel ID or @handle")
    parser.add_argument("--max", type=int, default=40, help="Max videos to process (default: 40)")
    parser.add_argument("--delay", type=int, default=5, help="Delay in seconds between videos (default: 5)")
    parser.add_argument("--reframe-style", type=str, default="smart_face_track", choices=["smart_face_track", "blur_stack", "center_crop"], help="Reframe mode")
    args = parser.parse_args()

    run_migration(
        channel_id=args.channel_id,
        max_videos=args.max,
        delay_seconds=args.delay,
        reframe_style=args.reframe_style
    )
