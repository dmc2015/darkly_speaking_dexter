def parse_line(self, text: str, line_number: int) -> Optional[Dict]:
    """Parse a single line of dialogue."""
    text = self.clean_text(text)
    if not text:
        return None

    #######  OLD
    # Check for context markers
    # if text.startswith('[') and any(context_word.lower() in text.lower()
    #                               for context_word in (self.sound_effect_words + self.action_words)):
    #     # return {
    #     #     "context": [text],
    #     #     "line_number": line_number
    #     # }
    #     content = text[1:-1].strip()  # Remove the brackets
    #     self.context_buffer.append(content)
    #     return None

    ######## OLD

    # if text.startswith('[') and text.endswith(']'):
    #     content = text[1:-1].strip()  # Remove the brackets
    #     words = content.split()

    #     # Check each word to see if it's a character name
    #     speaker_name = None
    #     context_words = []

    #     for word in words:
    #         if word in self.name_normalizer.case_insensitive_mappings:
    #             speaker_name = word
    #         elif word.lower() in (w.lower() for w in (self.sound_effect_words + self.action_words)):
    #             context_words.append(word)

    #     if context_words:
    #         self.context_buffer.extend(context_words)

    #     if speaker_name:
    #         self.current_speaker = self.name_normalizer.normalize(speaker_name)

    #     return None

    #######
    # if text.startswith('[') and text.endswith(']'):
    #     content = text[1:-1].strip()  # Remove the brackets
    #     words = content.split()

    #     # Check each word to see if it's a character name
    #     speaker_name = None
    #     context_words = []

    #     for word in words:
    #         if word in self.name_normalizer.case_insensitive_mappings:
    #             speaker_name = word
    #         elif any(action.lower() in word.lower() for action in self.action_words):
    #             context_words.append(word)
    #         elif any(sound.lower() in word.lower() for sound in self.sound_effect_words):
    #             context_words.append(word)

    #     if context_words:
    #         self.context_buffer.extend(context_words)

    #     if speaker_name:
    #         self.current_speaker = self.name_normalizer.normalize(speaker_name)
    #     return None
    #######

    #######
    # Add entry state logging
    self.logger.debug(f"[Line {line_number}] Processing line: {text}")
    self.logger.debug(
        f"[Line {line_number}] Current speaker at start: {self.current_speaker}"
    )

    if text.startswith("[") and text.endswith("]"):
        content = text[1:-1].strip()
        words = content.split()

        self.logger.debug(f"[Line {line_number}] Processing bracketed text: {content}")
        self.logger.debug(f"[Line {line_number}] Words to process: {words}")

        speaker_name = None
        context_words = []

        for word in words:
            normalized_word = word.upper()
            if normalized_word in self.name_normalizer.case_insensitive_mappings:
                speaker_name = normalized_word
                self.logger.debug(
                    f"[Line {line_number}] Found potential speaker: {speaker_name}"
                )
            elif any(action.lower() in word.lower() for action in self.action_words):
                context_words.append(word)
                self.logger.debug(f"[Line {line_number}] Added action word: {word}")
            elif any(
                sound.lower() in word.lower() for sound in self.sound_effect_words
            ):
                context_words.append(word)
                self.logger.debug(f"[Line {line_number}] Added sound effect: {word}")

        if context_words:
            self.context_buffer.extend(context_words)
            self.logger.debug(
                f"[Line {line_number}] Updated context buffer: {self.context_buffer}"
            )

        if speaker_name:
            previous_speaker = self.current_speaker
            self.current_speaker = self.name_normalizer.normalize(speaker_name)
            self.logger.debug(
                f"[Line {line_number}] Speaker change: {previous_speaker} -> {self.current_speaker}"
            )

        self.logger.debug(
            f"[Line {line_number}] Current speaker after processing: {self.current_speaker}"
        )
        return None
    #######

    print(f"\nText: '{text}'")
    print(f"Starts with [: {text.startswith('[')}")
    print(f"Ends with ]: {text.endswith(']')}")
    print(f"Length: {len(text)}")
    #######
    if text.startswith("[") and text.endswith("]"):
        content = text[1:-1].strip()  # Remove the brackets
        words = content.split()
        print("don")

        # Debug prints
        print(f"\n=== Processing Line: {text} ===")
        print(f"Current speaker before: {self.current_speaker}")

        # Check each word to see if it's a character name
        speaker_name = None
        context_words = []

        for word in words:
            word_upper = word.upper()
            if word_upper in self.name_normalizer.case_insensitive_mappings:
                speaker_name = word_upper
                print(f"Found character name: {word_upper}")
            elif any(action.lower() in word.lower() for action in self.action_words):
                context_words.append(word)
                print(f"Found action word: {word}")
            elif any(
                sound.lower() in word.lower() for sound in self.sound_effect_words
            ):
                context_words.append(word)
                print(f"Found sound effect: {word}")

        if context_words:
            self.context_buffer.extend(context_words)
            print(f"Updated context buffer: {self.context_buffer}")

        if speaker_name:
            self.current_speaker = self.name_normalizer.normalize(speaker_name)
            print(f"Updated speaker to: {self.current_speaker}")

        print(f"Current speaker after: {self.current_speaker}")
        print("===========================\n")
        return None
    #######

    # First check for speaker in brackets
    speaker, remaining_text = self.is_speaker_line(text)

    if speaker:
        speaker_info = self.name_normalizer.get_speaker_info(speaker)
        self.current_speaker = speaker_info["normalized_name"]
        if remaining_text:
            return {
                "speaker": speaker_info["normalized_name"],
                "original_speaker": speaker_info["original_name"],
                "text": remaining_text,
                "type": speaker_info["type"],
                "line_number": line_number,
            }

    # Then check for direct speaker introduction
    if not speaker:
        speaker, full_text = self.is_direct_speaker_introduction(text)
        if speaker:
            speaker_info = self.name_normalizer.get_speaker_info(speaker)
            self.current_speaker = speaker_info["normalized_name"]
            return {
                "speaker": speaker_info["normalized_name"],
                "original_speaker": speaker_info["original_name"],
                "text": full_text,
                "type": speaker_info["type"],
                "line_number": line_number,
            }

    # If we have a current speaker, attribute the line to them
    if self.current_speaker and text:
        dialogue_entry = {
            "speaker": self.current_speaker,
            "original_speaker": self.current_speaker,
            "text": text,
            "type": "spoken",
            "line_number": line_number,
        }
        if self.context_buffer:  # Add context if we have any
            dialogue_entry["context"] = self.context_buffer.copy()
            self.context_buffer.clear()  # Clear after using
        return dialogue_entry

    # Check for other context-like lines (e.g., "Population: , .")
    if ":" in text and len(text.split(":", 1)[0].strip().split()) <= 2:
        return {"context": [text], "line_number": line_number}

    return None
