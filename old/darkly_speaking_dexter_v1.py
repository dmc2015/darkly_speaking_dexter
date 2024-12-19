import requests
from bs4 import BeautifulSoup, NavigableString, Tag
import json
import time
import random
import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin
from pathlib import Path
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from utils.character_name import CharacterNormalizer


class DexterScraper:
    def __init__(
        self,
        base_url: str = "https://transcripts.foreverdreaming.org/viewforum.php?f=187",
    ):
        self.base_url = base_url
        self.episodes_data: List[Dict] = []
        self.current_speaker = None
        self.normalizer = CharacterNormalizer()

        # Configure session with retries
        self.session = requests.Session()
        retries = Retry(
            total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504]
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retries))

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler("logs/scraper.log"), logging.StreamHandler()],
        )
        self.logger = logging.getLogger(__name__)

    def clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        text = re.sub(r"\s+", " ", text)
        text = text.replace("_", "")
        text = re.sub(r"\[\s*\]", "", text)
        text = re.sub(r"-+", "-", text)
        text = re.sub(r"^\s*-\s*|\s*-\s*$", "", text)
        return text.strip()

    def get_episode_links(self) -> List[str]:
        """Retrieve all episode transcript links."""
        try:
            response = self.session.get(self.base_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            topics_anchor = soup.find("a", {"class": "forum-name"}, text="Topics")
            if not topics_anchor:
                self.logger.error("Could not find Topics anchor")
                return []

            topics_h2 = topics_anchor.find_parent("h2")
            if not topics_h2:
                self.logger.error("Could not find h2 parent")
                return []

            topics_ul = topics_h2.find_next_sibling("ul", {"class": "topics"})
            if not topics_ul:
                self.logger.error("Could not find topics list")
                return []

            links = topics_ul.find_all("a", {"class": "topictitle"})
            if not links:
                self.logger.warning("No episode links found")
                return []

            episode_links = [
                urljoin(self.base_url, link["href"])
                for link in links
                if link.get("href")
            ]
            self.logger.info(f"Found {len(episode_links)} episode links")
            return episode_links

        except requests.RequestException as e:
            self.logger.error(f"Failed to get episode links: {e}")
            return []

    def process_html_content(self, content: Tag) -> List[str]:
        """Process HTML content and extract lines."""
        lines = []
        current_line = []

        for element in content.children:
            if isinstance(element, NavigableString):
                text = str(element).strip()
                if text:
                    current_line.append(text)
            elif element.name == "br":
                if current_line:
                    lines.append(" ".join(current_line))
                    current_line = []

        if current_line:
            lines.append(" ".join(current_line))

        return [line for line in lines if line.strip()]

    def is_speaker_line(self, text: str) -> Tuple[Optional[str], str]:
        """Check if line contains a speaker name in brackets."""
        match = re.match(r"\[([^]]+)\](.*)", text.strip())
        if match:
            speaker, remaining = match.group(1), match.group(2)
            if not any(
                word.lower() in speaker.lower()
                for word in ["music", "rings", "click", "sound", "phone"]
            ):
                return speaker, remaining.strip()
        return None, text

    def parse_line(self, text: str, line_number: int) -> Optional[Dict]:
        """Parse a single line of transcript text."""
        text = self.clean_text(text)
        if not text:
            return None

        # Check for context markers
        if text.startswith("[") and any(
            word.lower() in text.lower()
            for word in ["music", "rings", "click", "sound", "phone"]
        ):
            return {"context": [text], "line_number": line_number}

        # Check for speaker in brackets
        speaker, remaining_text = self.is_speaker_line(text)
        if speaker:
            speaker_info = self.normalizer.get_speaker_info(speaker)
            self.current_speaker = speaker_info["normalized_name"]
            if remaining_text:
                return {
                    "speaker": speaker_info["normalized_name"],
                    "original_speaker": speaker_info["original_name"],
                    "text": remaining_text,
                    "type": speaker_info["type"],
                    "line_number": line_number,
                }

        # If we have a current speaker, attribute the line to them
        if self.current_speaker and text:
            return {
                "speaker": self.current_speaker,
                "original_speaker": self.current_speaker,
                "text": text,
                "type": "spoken",
                "line_number": line_number,
            }

        # Check for context-like lines
        if ":" in text and len(text.split(":", 1)[0].strip().split()) <= 2:
            return {"context": [text], "line_number": line_number}

        return None

    def parse_episode(self, url: str) -> Optional[Dict]:
        """Parse a complete episode transcript."""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            content = soup.find("div", class_="content") or soup.find(
                "div", class_="postbody"
            )
            if not content:
                self.logger.warning(f"No content found: {url}")
                return None

            self.current_speaker = None
            dialogue = []

            lines = self.process_html_content(content)
            for line_number, line in enumerate(lines, 1):
                parsed_line = self.parse_line(line, line_number)
                if parsed_line:
                    dialogue.append(parsed_line)

            title = soup.find("h2", class_="title") or soup.find("h3", class_="first")
            episode_title = title.text.strip() if title else Path(url).stem

            return {
                "title": episode_title,
                "url": url,
                "dialogue": dialogue,
                "metadata": {
                    "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "total_lines": len(dialogue),
                    "unique_speakers": len(
                        set(d["speaker"] for d in dialogue if "speaker" in d)
                    ),
                    "context_lines": len([d for d in dialogue if "context" in d]),
                },
            }

        except Exception as e:
            self.logger.error(f"Error parsing episode {url}: {e}")
            return None

    def scrape_all_episodes(self, delay: float = 2.5):
        """Scrape all available episodes."""
        episode_links = self.get_episode_links()
        if not episode_links:
            self.logger.error("No episodes found to scrape")
            return

        self.logger.info(f"Beginning to scrape {len(episode_links)} episodes")

        for idx, link in enumerate(episode_links, 1):
            self.logger.info(f"Scraping episode {idx}/{len(episode_links)}: {link}")
            try:
                if episode_data := self.parse_episode(link):
                    self.episodes_data.append(episode_data)
                    self.logger.info(f"Successfully scraped: {episode_data['title']}")
                time.sleep(delay + (random.random() * 0.5))
            except Exception as e:
                self.logger.error(f"Error scraping {link}: {e}")

    def save_to_json(self, filename: str = "data/dexter_transcripts.json"):
        """Validating scraped data prior to saving JSON file."""

        validator = TranscriptValidator()
        data = {"metadata": self._generate_metadata(), "episodes": self.episodes_data}

        is_valid, results = validator.validate_dataset(data)
        if not is_valid:
            self.logger.error("Validation failed:")
            for error in results["errors"]:
                self.logger.error(f"Error: {error}")
            for warning in results["warnings"]:
                self.logger.warning(f"Warning: {warning}")
            raise ValueError("Dataset validation failed")

        """Save scraped data to JSON file."""

        try:
            output_path = Path(filename)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            metadata = {
                "total_episodes": len(self.episodes_data),
                "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "source": self.base_url,
                "total_dialogue_lines": sum(
                    len(ep["dialogue"]) for ep in self.episodes_data
                ),
                "unique_speakers": len(
                    set(
                        d["speaker"]
                        for ep in self.episodes_data
                        for d in ep["dialogue"]
                        if "speaker" in d
                    )
                ),
            }

            with output_path.open("w", encoding="utf-8") as f:
                json.dump(
                    {"metadata": metadata, "episodes": self.episodes_data},
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

            self.logger.info(f"Successfully saved data to {filename}")
        except Exception as e:
            self.logger.error(f"Failed to save data: {e}")
            raise


if __name__ == "__main__":
    scraper = DexterScraper()
    scraper.scrape_all_episodes()
    scraper.save_to_json()
