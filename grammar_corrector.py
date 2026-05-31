"""
grammar_corrector.py - Post-processing Grammar Correction Layer

ARCHITECTURE: Rule-based grammar correction (NO ML changes, NO model modifications)
- Applied AFTER sentence buffer completion
- Lightweight pattern matching and rule application
- Optionally extensible to ML-based correction later
- Pure functional: input sentence → corrected sentence

FLOW: predictions → sentence builder → grammar correction → final display
"""

import re
from typing import List, Tuple


class GrammarCorrector:
    """Rule-based grammar correction for sign language translation output."""

    def __init__(self):
        """Initialize grammar rules and patterns."""
        # Common phrase patterns to fix
        self.phrase_mappings = {
            "how you": "how are you",
            "how i": "how am i",
            "how we": "how are we",
            "what you": "what are you",
            "what i": "what am i",
            "what we": "what are we",
            "who you": "who are you",
            "who i": "who am i",
            "who we": "who are we",
        }

        # Words that need a verb after them
        self.needs_verb_after = {
            "my": "is",
            "your": "is",
            "his": "is",
            "her": "is",
            "its": "is",
            "the": "is",
            "i": "am",
            "you": "are",
            "he": "is",
            "she": "is",
            "we": "are",
            "they": "are",
        }

        # Common corrections
        self.word_corrections = {
            "ur": "your",
            "u": "you",
            "im": "i'm",
            "dont": "don't",
            "cant": "can't",
            "wont": "won't",
        }

    def correct_sentence(self, sentence: str) -> str:
        """
        Apply grammar corrections to a sentence.

        Args:
            sentence: Raw sentence from translator (e.g., "how you", "my major computer science")

        Returns:
            Grammar-corrected sentence (e.g., "How are you?", "My major is computer science.")
        """
        if not sentence or not isinstance(sentence, str):
            return sentence

        # Trim whitespace
        sentence = sentence.strip()
        if not sentence:
            return sentence

        # Step 1: Apply phrase-level corrections (most common patterns)
        sentence = self._apply_phrase_mappings(sentence)

        # Step 2: Fix missing verbs in patterns
        sentence = self._fix_missing_verbs(sentence)

        # Step 3: Capitalize first letter
        sentence = self._capitalize_sentence(sentence)

        # Step 4: Add ending punctuation if missing
        sentence = self._add_ending_punctuation(sentence)

        return sentence

    def _apply_phrase_mappings(self, sentence: str) -> str:
        """Replace common phrase patterns."""
        words = sentence.lower().split()
        sentence_lower = " ".join(words)

        for pattern, replacement in self.phrase_mappings.items():
            # Use word boundary matching to avoid partial replacements
            sentence_lower = re.sub(
                r'\b' + re.escape(pattern) + r'\b',
                replacement,
                sentence_lower,
                flags=re.IGNORECASE
            )

        return sentence_lower

    def _fix_missing_verbs(self, sentence: str) -> str:
        """
        Fix patterns where a verb (is, are, am) is missing.

        Examples:
            "i tired" → "I am tired"
            "my major computer science" → "my major is computer science"
            "your name john" → "your name is john"
        """
        words = sentence.split()
        
        if len(words) < 2:
            return sentence

        result = []
        i = 0
        while i < len(words):
            word = words[i]
            result.append(word)

            # Case 1: Pronouns that need a verb after them directly
            # e.g., "i tired" → "i am tired"
            if word.lower() in ["i", "you", "we", "they", "he", "she", "it"]:
                if i + 1 < len(words):
                    next_word = words[i + 1].lower()
                    # If next word is NOT a verb, insert one
                    if not self._is_verb(next_word):
                        verb = self._get_appropriate_verb(word.lower())
                        result.append(verb)
            
            # Case 2: Possessives/articles followed by noun + more words
            # e.g., "my major computer science" → "my major is computer science"
            elif word.lower() in ["my", "your", "his", "her", "its", "the"]:
                if i + 2 < len(words):
                    second_word = words[i + 1].lower()
                    third_word = words[i + 2].lower()
                    # If second word is NOT a verb and third word is NOT a verb
                    # (pattern: "my noun noun" needs a verb)
                    if not self._is_verb(second_word) and not self._is_verb(third_word):
                        # Add the second word first, then insert verb
                        result.append(words[i + 1])
                        verb = self._get_appropriate_verb(word.lower())
                        result.append(verb)
                        i += 1  # Skip the next word since we already added it
            
            i += 1

        return " ".join(result)

    def _fix_interrogative(self, sentence: str) -> str:
        """
        Fix interrogative patterns (how, what, who, which).

        Examples:
            "how you" → "how are you"
            "what i doing" → "what am i doing"
        """
        words = sentence.split()
        if len(words) < 2:
            return sentence

        # Check first word for interrogatives
        first_word = words[0].lower()
        if first_word in ["how", "what", "who", "which"]:
            if len(words) >= 2:
                second_word = words[1].lower()
                # If second word is a pronoun/noun, we might need a verb
                if second_word in self.needs_verb_after:
                    if len(words) < 3 or not self._is_verb(words[2].lower()):
                        # Insert appropriate verb
                        verb = self._get_appropriate_verb(second_word)
                        words.insert(2, verb)

        return " ".join(words)

    def _is_verb(self, word: str) -> bool:
        """Check if a word is likely a verb."""
        verbs = {
            "is", "are", "am", "was", "were",
            "be", "been", "being",
            "have", "has", "had",
            "do", "does", "did",
            "will", "would", "can", "could", "may", "might", "must", "should",
            "going", "doing", "being", "having",
            "eat", "eating", "like", "liking", "want", "wanting",
            "need", "needing", "help", "helping",
            "understand", "understanding", "know", "knowing",
            "see", "seeing", "hear", "hearing",
            "look", "looking", "find", "finding", "give", "giving",
            "come", "coming", "go", "going", "make", "making",
            "work", "working", "use", "using", "try", "trying",
            "wait", "waiting", "feel", "feeling", "put", "putting",
            "say", "saying", "speak", "speaking", "ask", "asking",
            "think", "thinking", "show", "showing", "tell", "telling",
        }
        return word in verbs or word.endswith("ing")

    def _get_appropriate_verb(self, pronoun: str) -> str:
        """Get the appropriate verb for a pronoun."""
        pronouns_to_verb = {
            "i": "am",
            "you": "are",
            "he": "is",
            "she": "is",
            "it": "is",
            "we": "are",
            "they": "are",
            # possessives need 'is'
            "my": "is",
            "your": "is",
            "his": "is",
            "her": "is",
            "its": "is",
            "the": "is",
        }
        return pronouns_to_verb.get(pronoun.lower(), "is")

    def _capitalize_sentence(self, sentence: str) -> str:
        """Capitalize the first letter of the sentence."""
        if not sentence:
            return sentence
        return sentence[0].upper() + sentence[1:] if len(sentence) > 1 else sentence.upper()

    def _add_ending_punctuation(self, sentence: str) -> str:
        """Add appropriate ending punctuation if missing."""
        if not sentence:
            return sentence

        # Check if sentence already has ending punctuation
        if sentence[-1] not in ".!?":
            # Check if it's a question
            if sentence.lower().startswith(("how", "what", "who", "which", "why", "when", "where", "do ", "does ", "did ", "can ", "could ", "will ", "would ")):
                sentence += "?"
            else:
                sentence += "."

        return sentence


# Singleton instance
_corrector = None


def get_corrector() -> GrammarCorrector:
    """Get or create the grammar corrector singleton."""
    global _corrector
    if _corrector is None:
        _corrector = GrammarCorrector()
    return _corrector


def correct_sentence(sentence: str) -> str:
    """
    Correct grammar in a sentence from sign language translation.

    This is the main entry point for grammar correction.

    Args:
        sentence: Raw sentence from translator (word-separated string)

    Returns:
        Grammar-corrected sentence with proper verbs, capitalization, and punctuation

    Examples:
        >>> correct_sentence("how you")
        'How are you?'

        >>> correct_sentence("my major computer science")
        'My major is computer science.'

        >>> correct_sentence("i tired")
        'I am tired.'
    """
    corrector = get_corrector()
    return corrector.correct_sentence(sentence)


# For testing
if __name__ == "__main__":
    test_sentences = [
        "how you",
        "my major computer science",
        "what you doing",
        "i tired",
        "your name john",
        "we happy",
        "they nice people",
        "my name is alice",
        "how i look",
        "what we eating",
    ]

    corrector = GrammarCorrector()
    print("Grammar Correction Examples:")
    print("-" * 60)
    for raw in test_sentences:
        corrected = corrector.correct_sentence(raw)
        print(f"Raw:       {raw}")
        print(f"Corrected: {corrected}")
        print()
