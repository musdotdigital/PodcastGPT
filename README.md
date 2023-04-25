# PodcastGPT

PodcastGPT downloads, transcribes, and answers questions on any podcast given a link. Letting you extract all the key takeaways from your favourite podcasts.

## Prerequisites

1. Install required packages: Run `pip install -r requirements.txt`
2. Add the [ChromeDriver](https://chromedriver.chromium.org/downloads) to the root of the project folder.
3. Set the `OPENAI_API_KEY` in your `.bashrc` or `.zshrc` file.

## Usage

### Downloading a podcast

Currently, the `download.py` script supports downloading from Apple Podcast URLs. To download a podcast, run the following command, this will return the file name, which is downloaded to the root of the directory:

```bash
python download.py -u 'https://podcasts.apple.com/gb/podcast/y-combinator/id1236907421?i=1000610561547'
```

### Transcribing and saving embeddings to ask questions

After downloading the podcast, you can transcribe, save the embeddings for retrieval and ask questions to the podcast with `ask.py` using the following command, (this works for any `.mp3` file):

```bash
python ask.py -f The_Students_Guide_To_Becoming_A_Successful_Startup_Founder.mp3
```

### Example Use:

```bash
Ask a question: tell me about anecdotes about startups and high schoolers

The podcast discusses how many high schoolers are interested in startups and the tech world, and how some even anonymously participate in startups on Discord. The hosts encourage high schoolers to learn skills like coding, design, and launching products, and to be honest with themselves and others. They also emphasize the importance of playing the long game and being patient in pursuing their dreams. The hosts give examples of successful people who started pursuing their dreams in high school, such as the creators of a music recommendation plugin for Winamp. They also share personal anecdotes about their own experiences with startups and the importance of honesty in the industry.
```

### Contributing

We welcome contributions to PodcastGPT! This is a lightweight application for embeddings and AI querying, it is designed to help you understand embedding applications and how they work at their core. Please feel free to submit pull requests or open issues with any suggestions or improvements.
