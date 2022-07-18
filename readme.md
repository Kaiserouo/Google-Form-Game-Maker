# Google Form Game Maker

Inspired from [this anonymous plurk](https://www.plurk.com/p/ox2otv) about a game made by Google Form.

Tackles nasty things like Google Form API and defines all kinds of items and interfaces in `util.py`, so you can make your own game more easily based on that.

## Uh why do I need that?
Making a game out of Google Form is basically realizing a finite state machine (FSM) in Google Form. And we know FSM can be very large in size, and in gaming, it's mostly because you interact with the world and the world changes.

e.g. After you pressed the "open door" button, the door opens, but to reflect world state change, you need to copy a lot of sections in Google Form to embed the information that the button is pressed and the door opened.

![](https://images.plurk.com/6CTRxAvVj8tLQ8KHHh64Es.png)

That would be hard to do by hand, especially since the copies you need is proportional to $2^{b}$, where $b$ is the count of bits needed to represent a world state.

## So how do I use this?

Refers to `simple_game.py` for how to write your own game.

Note that this needs a Google Cloud Platform project with the API enabled, and a credentials. Follow the guide below and make sure you can run the example code.

https://developers.google.com/forms/api/quickstart/python

The credentials, after downloading as a JSON file, you need to rename that to `client_secrets.json` and put into this folder.

If you complete the guide above, execute this should make the simple game form.
```bash
python simple_game.py
```

Do note that **Google Cloud Platform is supposed to be a paid service. But [if your usage is under the Free Tier limits you should be fine](https://cloud.google.com/free).** At least I did not paid for this. This application shouldn't use too much quota.
