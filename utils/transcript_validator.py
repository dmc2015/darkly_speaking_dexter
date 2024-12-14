from typing import Dict, List, Tuple
from datetime import datetime
import pdb


class TranscriptValidator:
    def __init__(self):
        self.validation_errors: List[str] = []
        self.validation_warnings: List[str] = []

        # Define expected fields and types
        self.episode_required_fields = {"title", "url", "dialogue", "metadata"}
        self.dialogue_required_fields = {"line_number"}
        self.metadata_required_fields = {"scraped_at", "total_lines", "unique_speakers"}

    def validate_episode(
        self, episode_data: Dict, metadata: Dict, episode_index: int
    ) -> Tuple[bool, List[str], List[str]]:
        """Validate a single episode's data structure and content."""
        self.validation_errors = []
        self.validation_warnings = []

        # Check required fields
        for field in self.episode_required_fields:
            if field not in episode_data:
                self.validation_errors.append(
                    f"Show: {metadata["show_name"]}, Season: {metadata["season"]}, Episode#: {metadata["episode"]}, Episode {episode_index}: Missing required field '{field}'"
                )

        if not self.validation_errors:
            # Validate title
            if not episode_data["title"] or not isinstance(episode_data["title"], str):
                # pdb.set_trace()
                self.validation_errors.append(
                    f"Show: {metadata["show_name"]}, Season: {metadata["season"]}, Episode#: {metadata["episode"]}, Episode {episode_index}: Invalid or empty title"
                )

            # Validate metadata
            self._validate_metadata(episode_data["metadata"], episode_index)

            # Validate dialogue
            self._validate_dialogue(episode_data["dialogue"], metadata, episode_index)
        return (
            not bool(self.validation_errors),
            self.validation_errors,
            self.validation_warnings,
        )

    def _validate_metadata(self, metadata: Dict, episode_index: int) -> None:
        """Validate episode metadata."""
        for field in self.metadata_required_fields:
            if field not in metadata:
                self.validation_errors.append(
                    f"Show: {metadata["show_name"]}, Season: {metadata["season"]}, Episode#: {metadata["episode"]}, Episode {episode_index}: Missing metadata field '{field}'"
                )
                return

        # Validate numerical fields
        if not isinstance(metadata["total_lines"], int) or metadata["total_lines"] < 0:
            self.validation_errors.append(
                f"Show: {metadata["show_name"]}, Season: {metadata["season"]}, Episode#: {metadata["episode"]}, Episode {episode_index}: Invalid total_lines count"
            )

        if (
            not isinstance(metadata["unique_speakers"], int)
            or metadata["unique_speakers"] < 0
        ):
            self.validation_errors.append(
                f"Show: {metadata["show_name"]}, Season: {metadata["season"]}, Episode#: {metadata["episode"]}, Episode {episode_index}: Invalid unique_speakers count"
            )

    def _validate_dialogue(
        self, dialogue: List[Dict], metadata: Dict, episode_index: int
    ) -> None:
        """Validate dialogue entries."""
        if not dialogue:
            self.validation_warnings.append(
                f"Show: {metadata["show_name"]}, Season: {metadata["season"]}, Episode#: {metadata["episode"]}, Episode {episode_index}: Empty dialogue list"
            )
            return

        line_numbers = set()
        current_speaker = None
        consecutive_empty_speakers = 0

        for i, entry in enumerate(dialogue):
            # Check line number sequence
            if "line_number" not in entry:
                self.validation_errors.append(
                    f"Show: {metadata["show_name"]}, Season: {metadata["season"]}, Episode#: {metadata["episode"]}, Episode {episode_index}: Missing line number at position {i}"
                )
            else:
                if entry["line_number"] in line_numbers:
                    self.validation_errors.append(
                        f"Show: {metadata["show_name"]}, Season: {metadata["season"]}, Episode#: {metadata["episode"]}, Episode {episode_index}: Duplicate line number {entry['line_number']}"
                    )
                line_numbers.add(entry["line_number"])

            if "speaker" not in entry or "text" not in entry or "type" not in entry:
                self.validation_warnings.append(
                    f"Show: {metadata["show_name"]}, Season: {metadata["season"]}, Episode#: {metadata["episode"]}, Episode {episode_index}: Missing required dialogue fields at line {entry['line_number']}"
                )
            else:
                # Track speaker consistency
                if entry["speaker"] != current_speaker:
                    consecutive_empty_speakers = 0
                    current_speaker = entry["speaker"]
                else:
                    consecutive_empty_speakers += 1
                    if consecutive_empty_speakers > 5:
                        self.validation_warnings.append(
                            f"Show: {metadata['show_name']}, Season: {metadata['season']}, Episode#: {metadata['episode']}, Episode {episode_index}: Possible missing speaker attribution "
                            f"around line {entry['line_number']}"
                        )

                # Validate dialogue type
                if entry["type"] not in {"spoken", "voiceover"}:
                    self.validation_warnings.append(
                        f"Show: {metadata["show_name"]}, Season: {metadata["season"]}, Episode#: {metadata["episode"]}, Episode {episode_index}: Invalid dialogue type '{entry['type']}' "
                        f"at line {entry['line_number']}"
                    )

    def validate_dataset(self, data: Dict) -> Tuple[bool, Dict[str, List[str]]]:
        """Validate the entire transcript dataset."""
        if (
            not isinstance(data, dict)
            or "metadata" not in data
            or "episodes" not in data
        ):
            return False, {
                "errors": ["Invalid dataset structure: missing metadata or episodes"],
                "warnings": [],
            }

        all_errors = []
        all_warnings = []

        # Validate global metadata
        if not self._validate_global_metadata(data["metadata"]):
            all_errors.append("Invalid global metadata structure")

        # Validate each episode
        for i, episode in enumerate(data["episodes"]):
            # pdb.set_trace()
            is_valid, errors, warnings = self.validate_episode(
                episode, data["metadata"], i
            )
            all_errors.extend(errors)
            all_warnings.extend(warnings)

        return not bool(all_errors), {"errors": all_errors, "warnings": all_warnings}

    def _validate_global_metadata(self, metadata: Dict) -> bool:
        """Validate global dataset metadata."""
        required_fields = {
            "total_episodes",
            "scraped_at",
            "source",
            "total_dialogue_lines",
            "unique_speakers",
            "show_name",
            "season",
            "episode",
        }

        return all(field in metadata for field in required_fields)
