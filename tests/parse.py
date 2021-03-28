import unittest
from core.parse import *


class MetaRooPost(unittest.TestCase):
    def test_post(self):
        title = "Turkey vs. Grandma"
        body = "[Turkey vs. Grandma](https://www.reddit.com/r/coolguides/comments/meo1l2/how_to_reheat_pizza/gsl4arc?utm_source=share&utm_medium=web2x&context=5)"
        self.assertTrue(only_reddit_url(title, body))

    def test_post2(self):
        title = "Face vs Phone"
        body = "https://www.reddit.com/r/AskReddit/comments/fojhri/comment/flfwo4b?context=1"
        self.assertTrue(only_reddit_url(title, body))

    def test_post3(self):
        title = "Rice vs Myth"
        body = """Hope I did it right! 

https://www.reddit.com/r/AmItheAsshole/comments/m1h95d/comment/gqeqqaa"""
        self.assertTrue(only_reddit_url(title, body))

    def test_post4(self):
        title = "A real one this time, a chain break."
        body = """[https://www.reddit.com/r/NewsOfTheStupid/comments/i62l3u/nasa\_to\_remove\_offensive\_names\_from\_planets\_and/g0u4cvm/?context=3](https://www.reddit.com/r/NewsOfTheStupid/comments/i62l3u/nasa_to_remove_offensive_names_from_planets_and/g0u4cvm/?context=3)  


There it is. This time there is no fellow kind stranger leading me to a secret tunnel. Don’t see any Meta flair pop up, so I will post it here like this."""
        self.assertFalse(only_reddit_url(title, body))

    def test_blank_meta(self):
        title = "Mouthwash vs contact solution"
        body = ""
        self.assertTrue(only_reddit_url(title, body))

    def test_post5(self):
        title = "Crack in steel vs. Grand Canyon"
        body = "[https://old.reddit.com/r/interestingasfuck/comments/kufwec/crack\_in\_steel\_looks\_like\_grand\_canyon\_under/girr93v/?context=3](https://old.reddit.com/r/interestingasfuck/comments/kufwec/crack_in_steel_looks_like_grand_canyon_under/girr93v/?context=3)"
        self.assertTrue(only_reddit_url(title, body))

    def test_post6(self):
        title = "how do yall link to the previous post??"
        body = "asking for a friend"
        self.assertFalse(only_reddit_url(title, body))