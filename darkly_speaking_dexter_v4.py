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
from utils.transcript_validator import TranscriptValidator
import pdb


class DexterScraper:
    def __init__(
        self,
        base_url: str = "https://transcripts.foreverdreaming.org/viewforum.php?f=187",
    ):
        self.base_url = base_url
        self.episodes_data: List[Dict] = []
        self.current_speaker = None
        self.name_normalizer = CharacterNormalizer()

        # Configure session with retries
        self.session = requests.Session()
        retries = Retry(
            total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504]
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retries))

        self.sound_effect_words = [
            "music",
            "rings",
            "click",
            "sound",
            "phone",
            "DOOR OPENS",
            "EXHALES",
            "CLEARS THROAT",
            "TENSE MUSIC",
            "SNAPS FINGERS",
            "PHONE RINGING",
            "SIGHS",
            "SCOFFS",
            '"A WOLF AT THE DOOR" BY RADIOHEAD',
            "CAR ENGINE REVVING UP OUTSIDE",
            "CAR DOORS OPEN",
            "CAR DOORS OPEN",
            "DOOR CLOSES",
        ]
        self.action_words = [
            "grunting",
            "groaning",
            "grunts",
            "CHUCKLES",
            "laughter",
            "INDISTINCT",
            "chatter",
            "speaking spanish",
            "silverware",
            "clattering",
        ]
        self.context_buffer = []

        self.show_name = None
        self.season = None
        self.episode = None

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler("logs/scraper.log"), logging.StreamHandler()],
        )
        self.logger = logging.getLogger(__name__)

    def clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)
        # Remove underscores used for emphasis
        text = text.replace("_", "")
        # Remove empty brackets
        text = re.sub(r"\[\s*\]", "", text)
        # Clean up multiple dashes
        text = re.sub(r"-+", "-", text)
        # Remove standalone dashes at start/end
        text = re.sub(r"^\s*-\s*|\s*-\s*$", "", text)
        return text.strip()

    def get_episode_links(self) -> List[str]:
        """Retrieves all episode transcript links from the forum page."""
        try:
            ######
            response = self.session.get(self.base_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            # First find the "Topics" anchor
            topics_anchor = soup.find("a", {"class": "forum-name"}, text="Topics")
            if not topics_anchor:
                self.logger.error('Could not find "Topics" anchor')
                return []

            # Find its parent h2
            topics_h2 = topics_anchor.find_parent("h2")
            if not topics_h2:
                self.logger.error('Could not find h2 parent of "Topics" anchor')
                return []

            # Find the next ul.topics sibling after the h2
            topics_ul = topics_h2.find_next_sibling("ul", {"class": "topics"})
            if not topics_ul:
                self.logger.error("Could not find ul.topics after the h2")
                return []

            # Find all topictitle links within the topics ul
            links = topics_ul.find_all("a", {"class": "topictitle"})

            if not links:
                self.logger.warning("No episode links found within topics list")
                return []

            # Extract and process all hrefs
            episode_links = []
            for link in links:
                href = link.get("href")
                if href:
                    full_url = urljoin(self.base_url, href)
                    episode_links.append(full_url)

            self.logger.info(f"Found {len(episode_links)} episode links")
            return episode_links

        except requests.RequestException as e:
            self.logger.error(f"Failed to get episode links: {e}")
            return []

    def process_html_content(self, content: Tag) -> List[str]:
        """Process HTML content and extract lines, handling sentence continuations."""
        lines = []
        current_line = []
        sentence_buffer = []

        for element in content.children:
            if isinstance(element, NavigableString):
                text = str(element).strip()
                if text:
                    current_line.append(text)
            elif element.name == "br":
                if current_line:
                    text = " ".join(current_line)
                    # If we have buffered text and this doesn't look like a complete sentence
                    if (
                        sentence_buffer
                        and not text.strip()[-1] in ".!?\"')}]"
                        and not text.strip().endswith("...")
                    ):
                        sentence_buffer.append(text)
                    else:
                        # If we have buffered text, join it with current text
                        if sentence_buffer:
                            complete_line = " ".join(sentence_buffer + [text])
                            sentence_buffer = []
                            lines.append(complete_line)
                        else:
                            # Start a new buffer if this line looks incomplete
                            if not text.strip()[
                                -1
                            ] in ".!?\"')}]" and not text.strip().endswith("..."):
                                sentence_buffer = [text]
                            else:
                                lines.append(text)
                    current_line = []

        # Handle any remaining text
        if current_line:
            text = " ".join(current_line)
            if sentence_buffer:
                lines.append(" ".join(sentence_buffer + [text]))
            else:
                lines.append(text)
        elif sentence_buffer:
            lines.append(" ".join(sentence_buffer))

        return [line for line in lines if line.strip()]

    def is_speaker_line(self, text: str) -> Tuple[Optional[str], str]:
        """Check if line contains a speaker name in brackets and return speaker and remaining text."""
        match = re.match(r"\[([^]]+)\](.*)", text.strip())
        if match:
            potential_speaker = match.group(1)
            remaining_text = match.group(2)

            # Check if it's not a sound effect or music cue
            if not any(
                word.lower() in potential_speaker.lower()
                for word in ["music", "rings", "click", "sound", "phone"]
            ):
                return potential_speaker, remaining_text.strip()
        return None, text

    def is_direct_speaker_introduction(self, text: str) -> Tuple[Optional[str], str]:
        """Check if line directly introduces a speaker and return speaker and full text."""
        match = re.match(r"^This is ([^,:]+)(?:,|:|\s|$)(.*)", text.strip())
        if match:
            speaker = match.group(1)
            return speaker, text
        return None, text

    def parse_line(self, text: str, line_number: int) -> Optional[Dict]:
        """Parse a single line of dialogue."""

        text = self.clean_text(text)

        if not text:
            return None

        print(f"\nProcessing: '{text}'")
        # Check for bracketed content anywhere in the line

        bracket_start = text.find("[")
        bracket_end = text.find("]")

        if bracket_start != -1 and bracket_end != -1:
            # Extract the bracketed content
            bracketed_content = text[bracket_start + 1 : bracket_end].strip()
            remaining_text = text[bracket_end + 1 :].strip()


            # Split bracketed content into words
            words = bracketed_content.split()

            # Look for character name
            for word in words:
                word_upper = word.upper()
                if word_upper in self.name_normalizer.case_insensitive_mappings:
                    self.current_speaker = self.name_normalizer.normalize(word_upper)
                    print(f"Found speaker: {self.current_speaker}")  
                    words.remove(word)  # Remove the name from words
                    break

            # Any remaining words in brackets are context
            if words:
                self.context_buffer.extend(words)
                print(f"Added to context: {words}")

            # If there's remaining text, treat it as dialogue
            if remaining_text:
                dialogue_entry = {
                    "speaker": self.current_speaker,
                    "text": remaining_text,
                    "type": "spoken",
                    "line_number": line_number,
                }

                if self.context_buffer:
                    dialogue_entry["context"] = self.context_buffer.copy()
                    self.context_buffer.clear()
                return dialogue_entry
            return None

        speaker, remaining_text = self.is_speaker_line(text)
        if speaker:
            speaker_info = self.name_normalizer.get_speaker_info(speaker)
            self.current_speaker = speaker_info["normalized_name"]

            if self.context_buffer:
                context = self.context_buffer.copy()
                self.context_buffer.clear()
            else:
                context = []
            if remaining_text:
                return {
                    "speaker": speaker_info["normalized_name"],
                    "original_speaker": speaker_info["original_name"],
                    "text": remaining_text,
                    "context": context,
                    "type": speaker_info["type"],
                    "line_number": line_number,
                }

        # Then check for direct speaker introduction
        if not speaker:
            speaker, full_text = self.is_direct_speaker_introduction(text)
            if speaker:
                speaker_info = self.name_normalizer.get_speaker_info(speaker)
                self.current_speaker = speaker_info["normalized_name"]
                if self.context_buffer:
                    context = self.context_buffer.copy()
                    self.context_buffer.clear()
                else:
                    context = []
                return {
                    "speaker": speaker_info["normalized_name"],
                    "original_speaker": speaker_info["original_name"],
                    "text": full_text,
                    "context": context,
                    "type": speaker_info["type"],
                    "line_number": line_number,
                }

        # If we have a current speaker, attribute the line to them
        if self.current_speaker and text:
            if self.context_buffer:
                context = self.context_buffer.copy()
                self.context_buffer.clear()
            else:
                context = []
            return {
                "speaker": self.current_speaker,
                "original_speaker": self.current_speaker,
                "text": text,
                "type": "spoken",
                "context": context,
                "line_number": line_number,
            }

        # Check for other context-like lines (e.g., "Population: , .")
        if ":" in text and len(text.split(":", 1)[0].strip().split()) <= 2:
            return {"context": [text], "line_number": line_number}

        return None

    def parse_episode(self, url: str) -> Optional[Dict]:
        """Parse an individual episode transcript page."""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            # pdb.set_trace()

            episode_title_data = soup.find("h3", class_="first")

            # Extract the text from the tag
            text = episode_title_data.a.text

            # Split and parse the details
            series_title_season_episode, episode_title = text.split(" - ")
            if ":" in series_title_season_episode:
                series_subtitle, season_episode = series_title_season_episode.split(":")
                self.show_name = f"Dexter: {series_subtitle}"
                self.season, self.episode = (
                    string.strip() for string in season_episode.split("x")
                )
            else:
                self.season, self.episode = series_title_season_episode.split("x")
                self.show_name = "Dexter"

            content = soup.find("div", class_="content")
            if not content:
                content = soup.find("div", class_="postbody")

            if not content:
                self.logger.warning(f"No content found for episode: {url}")
                return None

            # Reset speaker for new episode
            self.current_speaker = None
            dialogue = []
            line_number = 0

            # Process HTML content preserving <br> tags
            lines = self.process_html_content(content)

            for line in lines:
                line_number += 1
                parsed_line = self.parse_line(line, line_number)
                if parsed_line:
                    dialogue.append(parsed_line)

            title = soup.find("h2", class_="title")
            if not title:
                title = soup.find("h3", class_="first")

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
                },
            }
        except requests.RequestException as e:
            self.logger.error(f"Failed to parse episode {url}: {e}")
            return None
        except Exception as e:
            pdb.set_trace()
            self.logger.error(f"Unexpected error parsing {url}: {e}")
            return None

    def scrape_all_episodes(self, delay: float = 2.5):
        """Scrape all episodes with error handling and progress tracking."""
        episode_links = self.get_episode_links()
        total_episodes = len(episode_links)

        if not total_episodes:
            self.logger.error("No episodes found to scrape")
            return

        self.logger.info(f"Beginning to scrape {total_episodes} episodes")

        for idx, link in enumerate(episode_links, 1):
            self.logger.info(f"Scraping episode {idx}/{total_episodes}: {link}")

            try:
                episode_data = self.parse_episode(link)
                if episode_data:
                    self.episodes_data.append(episode_data)
                    self.logger.info(
                        f"Successfully scraped episode: {episode_data['title']} "
                        f"({len(episode_data['dialogue'])} lines)"
                    )

                time.sleep(delay + (random.random() * 0.5))

            except Exception as e:
                self.logger.error(f"Error scraping {link}: {e}")
                continue

    def save_to_json(self, filename: str = "data/dexter_transcripts.json"):
        """Save scraped data to a JSON file."""
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
                "show_name": self.show_name,
                "season": self.season,
                "episode": self.episode,
            }

            data = {"metadata": metadata, "episodes": self.episodes_data[0:10]}

            # Validate data before saving
            validator = TranscriptValidator()

            is_valid, validation_results = validator.validate_dataset(data)

            if not is_valid:
                self.logger.error("Data validation failed:")
                for error in validation_results["errors"]:
                    self.logger.error(f"Error: {error}")
                for warning in validation_results["warnings"]:
                    self.logger.warning(f"Warning: {warning}")
                raise ValueError("Dataset validation failed")

            with output_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Successfully saved data to {filename}")
        except Exception as e:
            self.logger.error(f"Failed to save data to {filename}: {e}")
            raise


def main():
    scraper = DexterScraper()
    scraper.scrape_all_episodes()
    scraper.save_to_json()


if __name__ == "__main__":
    main()
