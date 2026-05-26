#!/usr/bin/env python3
"""LinkedIn Post Generator Agent - Main CLI Interface."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.markdown import Markdown
from rich.prompt import IntPrompt

from config import DRAFTS_DIR
from trends import trend_fetcher
from generator import post_generator
from linkedin import linkedin_browser

console = Console()


def print_banner():
    """Print application banner."""
    console.print(
        Panel.fit(
            "[bold blue]LinkedIn Post Generator Agent[/bold blue]\n"
            "[dim]AI-powered content creation for LinkedIn[/dim]",
            border_style="blue",
        )
    )
    console.print()


def show_menu():
    """Show main menu options."""
    console.print("[bold]What would you like to do?[/bold]\n")
    console.print("  [cyan]1[/cyan] Fetch trending topics")
    console.print("  [cyan]2[/cyan] Generate post from topic")
    console.print("  [cyan]3[/cyan] Review drafts")
    console.print("  [cyan]4[/cyan] Post to LinkedIn")
    console.print("  [cyan]5[/cyan] Analyze my writing style")
    console.print("  [cyan]0[/cyan] Exit")
    console.print()


async def fetch_trends():
    """Fetch and display trending topics."""
    console.print("[bold]Fetching trending topics...[/bold]\n")

    with console.status("Contacting trend sources..."):
        trends = trend_fetcher.get_trending_topics(limit=15)

    if not trends:
        console.print("[yellow]No trends found. Check your internet connection.[/yellow]")
        return

    # Save trends
    saved_path = trend_fetcher.save_trends(trends)
    console.print(f"[dim]Saved to: {saved_path}[/dim]\n")

    # Display trends
    table = Table(title="Trending Topics", show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=4)
    table.add_column("Topic", style="bold", width=50)
    table.add_column("Source", width=20)
    table.add_column("Angle Suggestions", width=30)

    for i, trend in enumerate(trends, 1):
        angles = trend.get("suggested_angles", [])
        angle_text = angles[0] if angles else "-"
        table.add_row(
            str(i),
            trend["topic"][:50],
            trend["source"],
            angle_text[:30] + "..." if len(angle_text) > 30 else angle_text,
        )

    console.print(table)
    console.print()


async def generate_post():
    """Generate a post from a topic."""
    console.print("[bold]Generate LinkedIn Post[/bold]\n")

    # Get topic from user
    topic = Prompt.ask("Enter the topic or trend to write about")

    # Get optional context
    use_context = Confirm.ask("Do you want to include recent trends as context?", default=True)
    trend_context = None

    if use_context:
        recent_trends = trend_fetcher.load_saved_trends()
        if recent_trends:
            trend_context = ", ".join([t["topic"] for t in recent_trends[:5]])
            console.print(f"[dim]Using trend context: {trend_context[:100]}...[/dim]\n")

    # Get content angle
    console.print("\nChoose a content angle:")
    console.print("  1. Share a personal learning")
    console.print("  2. Challenge a misconception")
    console.print("  3. Make a bold prediction")
    console.print("  4. Tell a story")
    console.print("  5. Let AI decide")

    angle_choice = IntPrompt.ask("Select angle", choices=["1", "2", "3", "4", "5"], default=5)
    angles = {
        "1": "Share a personal learning or 'aha' moment",
        "2": "Challenge a common misconception in the industry",
        "3": "Make a bold prediction about the future",
        "4": "Tell a relevant story with a lesson",
        "5": None,
    }
    angle = angles.get(str(angle_choice))

    with console.status("Generating post..."):
        post = post_generator.generate_post(topic, trend_context, angle)

    console.print()
    console.print(Panel(post, title="Generated Post", border_style="green"))
    console.print()

    # Save as draft
    if Confirm.ask("Save this as a draft?", default=True):
        filepath = post_generator.save_draft(post, topic)
        console.print(f"[green]Draft saved to: {filepath}[/green]")


async def review_drafts():
    """Review and edit pending drafts."""
    drafts = post_generator.get_pending_drafts()

    if not drafts:
        console.print("[yellow]No pending drafts found.[/yellow]")
        return

    console.print(f"[bold]Found {len(drafts)} pending draft(s)[/bold]\n")

    for i, draft in enumerate(drafts, 1):
        console.print(
            Panel(
                f"[dim]Topic:[/dim] {draft['topic']}\n"
                f"[dim]Created:[/dim] {draft['created_at']}\n"
                f"[dim]Length:[/dim] {draft['character_count']} characters\n\n"
                f"{draft['content']}",
                title=f"Draft #{i}",
                border_style="yellow",
            )
        )
        console.print()

        # Actions for this draft
        console.print("  [cyan]e[/cyan] Edit content")
        console.print("  [cyan]r[/cyan] Regenerate with same topic")
        console.print("  [cyan]d[/cyan] Delete draft")
        console.print("  [cyan]s[/cyan] Skip to next")
        console.print()

        action = Prompt.ask("Action", choices=["e", "r", "d", "s"], default="s")

        if action == "e":
            new_content = Prompt.ask("Enter edited content", default=draft["content"])
            draft["content"] = new_content
            draft["character_count"] = len(new_content)
            # Save edited draft
            with open(draft["filepath"], "w", encoding="utf-8") as f:
                import json
                json.dump(draft, f, indent=2)
            console.print("[green]Draft updated![/green]")

        elif action == "r":
            with console.status("Regenerating..."):
                new_post = post_generator.generate_post(draft["topic"])
            console.print(Panel(new_post, title="Regenerated Post", border_style="cyan"))
            if Confirm.ask("Replace draft with this version?", default=True):
                draft["content"] = new_post
                draft["character_count"] = len(new_post)
                with open(draft["filepath"], "w", encoding="utf-8") as f:
                    import json
                    json.dump(draft, f, indent=2)
                console.print("[green]Draft replaced![/green]")

        elif action == "d":
            if Confirm.ask("Delete this draft?", default=False):
                Path(draft["filepath"]).unlink()
                console.print("[yellow]Draft deleted.[/yellow]")
                drafts = post_generator.get_pending_drafts()  # Refresh list

        console.print("\n" + "-" * 50 + "\n")


async def post_to_linkedin():
    """Post a reviewed draft to LinkedIn."""
    console.print("[bold]Post to LinkedIn[/bold]\n")

    # Check credentials
    from config import LINKEDIN_EMAIL, LINKEDIN_PASSWORD
    if not LINKEDIN_EMAIL or not LINKEDIN_PASSWORD:
        console.print(
            "[red]LinkedIn credentials not configured.[/red]\n"
            "Please set LINKEDIN_EMAIL and LINKEDIN_PASSWORD in your .env file."
        )
        return

    # Get drafts ready to post
    drafts = post_generator.get_pending_drafts()
    reviewed_drafts = [d for d in drafts if d.get("status") == "reviewed"]

    if not reviewed_drafts:
        console.print("[yellow]No reviewed drafts found.[/yellow]")
        console.print("Please review drafts first before posting.")
        return

    console.print(f"[bold]{len(reviewed_drafts)}[/bold] draft(s) ready to post\n")

    for i, draft in enumerate(reviewed_drafts, 1):
        console.print(Panel(draft["content"], title=f"Draft #{i}: {draft['topic']}", border_style="cyan"))

        if Confirm.ask(f"Post draft #{i} to LinkedIn?", default=True):
            console.print("[dim]Launching browser...[/dim]\n")

            try:
                # Initialize browser (with headless=False for user to see)
                await linkedin_browser.initialize(headless=False)

                with console.status("Posting to LinkedIn..."):
                    success, result = await linkedin_browser.create_post(draft["content"])

                if success:
                    post_generator.mark_as_posted(draft["filepath"], result)
                    console.print(f"[green]Successfully posted![/green]")
                    console.print(f"[dim]URL: {result}[/dim]")
                else:
                    console.print(f"[red]Failed to post: {result}[/red]")

            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
            finally:
                await linkedin_browser.close()

        console.print()


async def analyze_style():
    """Analyze user's writing style from sample posts."""
    console.print("[bold]Writing Style Analysis[/bold]\n")
    console.print("Paste 3-5 of your past LinkedIn posts to analyze your writing style.\n")
    console.print("Enter each post on a new line. Type 'DONE' on a new line when finished.\n")

    posts = []
    while len(posts) < 3:
        line = Prompt.ask(f"Post #{len(posts) + 1}")
        if line.upper() == "DONE" and posts:
            break
        if line:
            posts.append(line)

    if not posts:
        console.print("[yellow]No posts provided for analysis.[/yellow]")
        return

    console.print("\n[dim]Analyzing writing style...[/dim]\n")

    try:
        profile = post_generator.analyze_writing_style(posts)

        console.print(
            Panel(
                f"[bold]Tone:[/bold] {profile.get('tone', 'N/A')}\n"
                f"[bold]Uses Emoji:[/bold] {profile.get('use_emoji', False)}\n"
                f"[bold]Typical Length:[/bold] {profile.get('typical_length', 'N/A')}\n"
                f"[bold]Structure:[/bold] {profile.get('preferred_structure', 'N/A')}\n"
                f"[bold]Voice Notes:[/bold] {profile.get('voice_notes', 'N/A')}",
                title="Your Style Profile",
                border_style="green",
            )
        )
        console.print("\n[green]Style profile saved! Future posts will match this style.[/green]")

    except Exception as e:
        console.print(f"[red]Error analyzing style: {e}[/red]")
        console.print("[dim]Make sure Ollama is running with a model installed.[/dim]")


async def main():
    """Main application loop."""
    print_banner()

    # Check Ollama connection
    from llm import llm_client
    if not llm_client._check_connection():
        console.print(
            "[yellow]Warning: Cannot connect to Ollama.[/yellow]\n"
            "Make sure Ollama is running: [cyan]ollama serve[/cyan]\n"
            "Install a model: [cyan]ollama pull llama3.2[/cyan]\n"
        )

    while True:
        show_menu()
        choice = Prompt.ask(
            "Enter choice",
            choices=["0", "1", "2", "3", "4", "5"],
            default="1",
        )

        if choice == "0":
            console.print("[blue]Goodbye![/blue]")
            break
        elif choice == "1":
            await fetch_trends()
        elif choice == "2":
            await generate_post()
        elif choice == "3":
            await review_drafts()
        elif choice == "4":
            await post_to_linkedin()
        elif choice == "5":
            await analyze_style()

        console.print()


if __name__ == "__main__":
    asyncio.run(main())
