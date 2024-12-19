import pandas as pd
import numpy as np
import json
from collections import Counter
from pathlib import Path
from typing import Dict, List, Set
from pprint import pprint


class TranscriptExplorer:
    def __init__(self, json_path: str = "data/dexter_transcripts.json"):
        with open(json_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)
        self.episodes = self.data["episodes"]

    def get_all_contexts(self) -> Counter:
        contexts = []
        for episode in self.episodes:
            for line in episode["dialogue"]:
                if "context" in line:
                    contexts.extend(line["context"])

        for context, count in Counter(contexts).items():
            print(f"{context}: {count}")

        return Counter(contexts)

    def get_speaker_stats(self) -> pd.DataFrame:
        speaker_data = []
        for episode in self.episodes:
            episode_speakers = Counter()
            for line in episode["dialogue"]:
                if "speaker" in line:
                    episode_speakers[line["speaker"]] += 1
            speaker_data.append(episode_speakers)

        return pd.DataFrame(speaker_data).fillna(0)

    def examine_contexts(self, top_n: int = 20) -> None:
        contexts = []
        for episode in self.episodes:
            for line in episode["dialogue"]:
                if "context" in line:
                    contexts.extend(line["context"])

        context_counts = Counter(contexts)

        print("\nTop Context Patterns:")
        print("-" * 50)
        print(f"{'Context':<30} | {'Count':>10} | {'% of Total':>10}")
        print("-" * 50)

        total_contexts = sum(context_counts.values())
        for context, count in context_counts.most_common(top_n):
            percentage = (count / total_contexts) * 100
            print(f"{context[:30]:<30} | {count:>10} | {percentage:>10.2f}%")

    def examine_speakers(self, min_lines: int = 10) -> None:
        speaker_lines = Counter()
        for episode in self.episodes:
            for line in episode["dialogue"]:
                if "speaker" in line:
                    speaker_lines[line["speaker"]] += 1

        print("\nSpeaker Statistics (minimum {} lines):".format(min_lines))
        print("-" * 60)
        print(f"{'Speaker':<30} | {'Total Lines':>10} | {'% of Dialogue':>15}")
        print("-" * 60)

        total_lines = sum(speaker_lines.values())
        for speaker, count in speaker_lines.most_common():
            if count >= min_lines:
                percentage = (count / total_lines) * 100
                print(f"{speaker[:30]:<30} | {count:>10} | {percentage:>15.2f}%")

    def find_potential_issues(self) -> None:
        long_speakers = []
        numeric_speakers = []
        suspicious_patterns = []

        for episode in self.episodes:
            for line in episode["dialogue"]:
                if "speaker" in line:
                    if len(line["speaker"].split()) > 4:
                        long_speakers.append((episode["title"], line["speaker"]))

                    if any(c.isdigit() for c in line["speaker"]):
                        numeric_speakers.append((episode["title"], line["speaker"]))

                    if len(line["speaker"]) > 50:
                        suspicious_patterns.append(
                            (
                                episode["title"],
                                "Very long speaker name",
                                line["speaker"],
                            )
                        )

        print("\nPotential Data Quality Issues:")
        print("\n1. Long Speaker Names (might be misclassified dialogue):")
        for episode, speaker in set(long_speakers):
            print(f"Episode: {episode}")
            print(f"Speaker: {speaker}")
            print("-" * 40)

        print("\n2. Speakers Containing Numbers (might be errors):")
        for episode, speaker in set(numeric_speakers):
            print(f"Episode: {episode}")
            print(f"Speaker: {speaker}")
            print("-" * 40)


"""

from data_explorer import TranscriptExplorer
explorer = TranscriptExplorer()

# Get context counts
contexts = explorer.get_all_contexts()
print(contexts.most_common(20))

# Get speaker statistics
speaker_stats = explorer.get_speaker_stats()
print(speaker_stats.describe())

explorer = TranscriptExplorer()
all_contexts = explorer.get_all_contexts()

# Print every single context with its count
for context, count in all_contexts.items():
    print(f"{context}: {count}")
    


"""
