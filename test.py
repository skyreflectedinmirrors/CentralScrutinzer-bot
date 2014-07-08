import praw
import multiprocessing


def print_post_title(post, title):
    print post.title, title


def main():
    Pool = multiprocessing.Pool()
    my_handler = praw.handlers.MultiprocessHandler()
    r = praw.Reddit(user_agent="simple-multi-threading-test", handler=my_handler)
    sub = r.get_subreddit("listentothis")
    source = sub.get_new(limit=100)

    posts = [source.next() for i in range(10)]
    titles = [post.title for post in posts]
    Pool.map(print_post_title, [posts, titles])
    Pool.close()
    Pool.join()


if __name__ == '__main__':
    main()