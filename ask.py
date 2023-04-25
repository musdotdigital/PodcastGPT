import ast
import os
import sys
import argparse
import openai
import tiktoken
from pydub import AudioSegment
import pandas as pd
from scipy import spatial

GPT_MODEL = "gpt-3.5-turbo"


def num_tokens(text: str, model: str = GPT_MODEL) -> int:
    """Return the number of tokens in a string."""
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))


def halved_by_delimiter(string: str, delimiter: str = "\n") -> list[str, str]:
    """Split a string in two, on a delimiter, trying to balance tokens on each side."""
    chunks = string.split(delimiter)
    if len(chunks) == 1:
        return [string, ""]  # no delimiter found
    elif len(chunks) == 2:
        return chunks  # no need to search for halfway point
    else:
        total_tokens = num_tokens(string)
        halfway = total_tokens // 2
        best_diff = halfway
        for i, chunk in enumerate(chunks):
            left = delimiter.join(chunks[: i + 1])
            left_tokens = num_tokens(left)
            diff = abs(halfway - left_tokens)
            if diff >= best_diff:
                break
            else:
                best_diff = diff
        left = delimiter.join(chunks[:i])
        right = delimiter.join(chunks[i:])
        return [left, right]


def truncated_string(
    string: str,
    model: str,
    max_tokens: int,
    print_warning: bool = True,
) -> str:
    """Truncate a string to a maximum number of tokens."""
    encoding = tiktoken.encoding_for_model(model)
    encoded_string = encoding.encode(string)
    truncated_string = encoding.decode(encoded_string[:max_tokens])
    if print_warning and len(encoded_string) > max_tokens:
        print(
            f"Warning: Truncated string from {len(encoded_string)} tokens to {max_tokens} tokens.")
    return truncated_string


def split_strings_from_subsection(
    subsection: tuple[list[str], str],
    max_tokens: int = 1000,
    model: str = GPT_MODEL,
    max_recursion: int = 5,
) -> list[str]:
    """
    Split a subsection into a list of subsections, each with no more than max_tokens.
    Each subsection is a tuple of parent titles [H1, H2, ...] and text (str).
    """
    text = subsection
    string = "\n\n".join([text])
    num_tokens_in_string = num_tokens(string)
    # if length is fine, return string
    if num_tokens_in_string <= max_tokens:
        return [string]
    # if recursion hasn't found a split after X iterations, just truncate
    elif max_recursion == 0:
        return [truncated_string(string, model=model, max_tokens=max_tokens)]
    # otherwise, split in half and recurse
    else:
        text = subsection
        for delimiter in ["\n\n", "\n", ". "]:
            left, right = halved_by_delimiter(text, delimiter=delimiter)
            if left == "" or right == "":
                # if either half is empty, retry with a more fine-grained delimiter
                continue
            else:
                # recurse on each half
                results = []
                for half in [left, right]:
                    half_subsection = (half)
                    half_strings = split_strings_from_subsection(
                        half_subsection,
                        max_tokens=max_tokens,
                        model=model,
                        max_recursion=max_recursion - 1,
                    )
                    results.extend(half_strings)
                return results
    # otherwise no split was found, so just truncate (should be very rare)
    return [truncated_string(string, model=model, max_tokens=max_tokens)]


def strings_ranked_by_relatedness(
    query: str,
    df: pd.DataFrame,
    relatedness_fn=lambda x, y: 1 - spatial.distance.cosine(x, y),
    top_n: int = 100
) -> tuple[list[str], list[float]]:
    """Returns a list of strings and relatednesses, sorted from most related to least."""
    query_embedding_response = openai.Embedding.create(
        model=EMBEDDING_MODEL,
        input=query,
    )
    query_embedding = query_embedding_response["data"][0]["embedding"]
    strings_and_relatednesses = [
        (row["text"], relatedness_fn(query_embedding, row["embedding"]))
        for i, row in df.iterrows()
    ]
    strings_and_relatednesses.sort(key=lambda x: x[1], reverse=True)
    strings, relatednesses = zip(*strings_and_relatednesses)
    return strings[:top_n], relatednesses[:top_n]


def num_tokens(text: str, model: str = GPT_MODEL) -> int:
    """Return the number of tokens in a string."""
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))


def query_message(
    query: str,
    df: pd.DataFrame,
    model: str,
    token_budget: int
) -> str:
    """Return a message for GPT, with relevant source texts pulled from a dataframe."""
    strings, relatednesses = strings_ranked_by_relatedness(query, df)
    introduction = 'You are a very enthusiastic podcast analyst who loves to help people! Given the podcast transcript, answer the question using the information provided as much as possible. If you are unsure and the answer is not explicitly written, tell the user that you are unsure, and that you would recommend they listen to the podcast again. Responses that are detailed, specific, nuanced and long will be rewarded.'
    question = f"\n\nQuestion: {query}"
    message = introduction
    for string in strings:
        next_article = f'\n\Podcast section:\n"""\n{string}\n"""'
        if (
            num_tokens(message + next_article + question, model=model)
            > token_budget
        ):
            break
        else:
            message += next_article
    return message + question


parser = argparse.ArgumentParser()
parser.add_argument('-f', '--file', type=str, required=True)
args = parser.parse_args()

PODCAST_FILE = args.file

if not PODCAST_FILE:
    print('Please provide a podcast file as an argument.')
    sys.exit()


print(f'Answering questions about the {PODCAST_FILE} podcast')
podcast = AudioSegment.from_mp3(PODCAST_FILE)

# PyDub handles time in milliseconds
ten_minute_chunk = 10 * 60 * 1000

# Create a directory to store the chunks
podcast_name = PODCAST_FILE.split('.mp3')[0]
chunk_dir = f'podcasts/{podcast_name}-chunks'
transcription_status = f'{chunk_dir}/transcription_status.txt'

if not os.path.exists(chunk_dir):
    os.mkdir(chunk_dir)

if not os.path.exists(transcription_status):
    # Loop through the podcast and split it into 10 minute chunks
    for i, chunk in enumerate(podcast[::ten_minute_chunk]):
        # Create the file name of the chunk
        chunk_name = f"{chunk_dir}/chunk{i}.mp3"
        # Export the chunk as a mp3 file
        print("exporting", chunk_name)
        chunk.export(chunk_name, format="mp3")

    # Loop through the chunks and transcribe them to a single text file
    for i, chunk in enumerate(podcast[::ten_minute_chunk]):
        # Create the file name of the chunk
        chunk_name = f"{chunk_dir}/chunk{i}.mp3"
        transcript_name = f"{chunk_dir}/transcript.txt"
        # Export the chunk as a mp3 file
        print("transcribing", chunk_name)
        audio_file = open(chunk_name, "rb")
        transcript = openai.Audio.transcribe("whisper-1", audio_file)

        if os.path.exists(transcript_name):  # optional check if file exists
            with open(transcript_name, 'a') as file:
                # could be any text, appended @ the end of file
                file.write(transcript['text'])
        else:
            with open(transcript_name, "w") as f:
                f.write(transcript['text'])

        # Create a file to mark all chunks have been transcribed after the last chunk
        if i == sum(1 for _ in (podcast[::ten_minute_chunk])) - 1:
            with open(transcription_status, "w") as f:
                f.write("complete")


# Read the transcript file
with open(f"{chunk_dir}/transcript.txt", "r") as f:
    text = f.read()

# Split the text into blocks of 1600 tokens
MAX_TOKENS = 1600
EMBEDDINGS_PATH = f"{chunk_dir}/embeddings.csv"

# OpenAI's best embeddings as of Apr 2023
EMBEDDING_MODEL = "text-embedding-ada-002"
BATCH_SIZE = 1000  # you can submit up to 2048 embedding inputs per request

if not os.path.exists(EMBEDDINGS_PATH):
    text_strings = []
    text_strings.extend(split_strings_from_subsection(
        text, max_tokens=MAX_TOKENS))
    print(f"Text split into {len(text_strings)} strings.")

    embeddings = []
    for batch_start in range(0, len(text_strings), BATCH_SIZE):
        batch_end = batch_start + BATCH_SIZE
        batch = text_strings[batch_start:batch_end]
        print(f"Batch {batch_start} to {batch_end-1}")
        response = openai.Embedding.create(model=EMBEDDING_MODEL, input=batch)
        for i, be in enumerate(response["data"]):
            # double check embeddings are in same order as input
            assert i == be["index"]
        batch_embeddings = [e["embedding"] for e in response["data"]]
        embeddings.extend(batch_embeddings)

    df = pd.DataFrame({"text": text_strings, "embedding": embeddings})

    df.to_csv(EMBEDDINGS_PATH, index=False)

# Read the embeddings file
df = pd.read_csv(EMBEDDINGS_PATH)
df['embedding'] = df['embedding'].apply(ast.literal_eval)


def ask(
    query: str,
    df: pd.DataFrame = df,
    model: str = GPT_MODEL,
    token_budget: int = 4096 - 500,
    print_message: bool = False,
) -> str:
    """Answers a query using GPT and a dataframe of relevant texts and embeddings."""
    message = query_message(query, df, model=model, token_budget=token_budget)
    if print_message:
        print(message)
    messages = [
        {"role": "system", "content": "You answer questions about podcasts when given the content of a podcast."},
        {"role": "user", "content": message},
    ]
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=0
    )
    response_message = response["choices"][0]["message"]["content"]
    return response_message


# Loop forever, asking questions and getting answers
while True:
    PODCAST_QUSTION = input("Ask a question: ")
    print(ask(PODCAST_QUSTION))
