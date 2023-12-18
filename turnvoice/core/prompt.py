from pydantic import BaseModel, Field, AfterValidator
from typing_extensions import Annotated
from openai import OpenAI
from typing import List
import instructor
import json

# Patching the OpenAI client with instructor functionalities.
client = instructor.patch(OpenAI())

# Global list to hold original sentence fragments.
original_sentence_fragments = []


class SentenceFragment(BaseModel):
    text_applied_tone: str = Field(
        ...,
        description="With applied tone change. "
                    "Keep original length under all circumstances.",
    )


def length_validator(
    changed_fragments: List[SentenceFragment]
) -> List[SentenceFragment]:
    """
    Validates that the length of the changed sentence fragments
    is within acceptable limits compared to the original fragments.
    """

    global original_sentence_fragments

    if len(original_sentence_fragments) != len(changed_fragments):
        raise ValueError("Number of sentence fragments must not change.")

    for index, changed_fragment in enumerate(changed_fragments):
        original_fragment_text = original_sentence_fragments[index]
        changed_fragment_text = changed_fragment.text_applied_tone

        changefactor = len(changed_fragment_text) / len(original_fragment_text)

        max_factor = 1.5
        min_factor = 0.666
        ok_distance = 7

        distance = abs(
            len(changed_fragment_text) - len(original_fragment_text)
        )

        if distance > ok_distance:
            if changefactor < min_factor:
                return_msg = f"Fragment {index} is too short compared to the "
                "original {original_fragment_text}. Make text "
                f"'{changed_fragment_text}' longer."

                print(return_msg)
                raise ValueError(return_msg)

            if changefactor > max_factor:
                return_msg = f"Fragment {index} is too long compared to the "
                f"original {original_fragment_text}. Make text "
                f"'{changed_fragment_text}' shorter."

                print(return_msg)
                raise ValueError(return_msg)

    print("All fragments have correct length.")
    return changed_fragments


class SentenceFragmentsResponse(BaseModel):
    sentence_fragments: Annotated[
        List[SentenceFragment],
        AfterValidator(length_validator)
    ]


def transform_fragments(
    sentence_fragments: List[str],
    change_prompt: str,
    full_sentence: str
) -> SentenceFragmentsResponse:
    """
    Transforms sentence fragments based on a given style or tone change,
    while preserving the original length of each fragment.
    """

    global original_sentence_fragments

    original_sentence_fragments = sentence_fragments
    message_list = [
        {
            "role": "system",
            "content": "Change the style or tone of the sentence fragments "
                       "while preserving their original text length in this "
                       f"way: {change_prompt}. Consider the full sentence "
                       "for context.",
        },
        {
            "role": "user",
            "content": f"Full Sentence: {full_sentence}",
        },
        {
            "role": "user",
            "content": f"Fragments: \n{json.dumps(sentence_fragments)}",
        }
    ]

    return client.chat.completions.create(
        model="gpt-4-1106-preview",
        max_retries=5,
        messages=message_list,
        response_model=SentenceFragmentsResponse,
    )


def frags_to_list(sentence_fragments) -> List[str]:
    """
    Converts a list of sentence fragment dictionaries to a list of strings.
    """
    return [fragment["text"] for fragment in sentence_fragments]


def transform_sentences(sentences, change_prompt: str):
    """
    Transforms a list of sentences based on a specified style or tone change,
    modifying each fragment while keeping their lengths consistent.
    """

    print(f"Starting to transform {len(sentences)} sentences.")
    print(f"Change prompt: {change_prompt}")

    for sentence_index, sentence in enumerate(sentences):
        frags_list = frags_to_list(sentence["sentence_frags"])

        try:
            frags = transform_fragments(
                frags_list,
                change_prompt,
                sentence["text"]
            )

            for index, fragment in enumerate(frags.sentence_fragments):

                print(f"Transformed fragment {index} from "
                      f'{sentence["sentence_frags"][index]["text"]}'
                      f'to {fragment.text_applied_tone}'
                      )

                new_text = fragment.text_applied_tone
                sentence["sentence_frags"][index]["text"] = new_text

        except ValueError as e:
            print(f'Error while transforming sentence {sentence_index} '
                  f'with text {sentence["text"]}: {e}'
                  )
            print("Probably not possible to apply style change without"
                  "changing the length of the sentence fragment.")
            print("Sentence frags keep unchanged.")
            continue
