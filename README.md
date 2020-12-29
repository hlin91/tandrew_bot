# tandrew_bot
My personal discord bot written to learn Python. Performs various miscellaneous functions including music playback, birthday notifications, wolfram-alpha queries, and wednesday-bot functionality.
<h3>Configuration</h3>
<p>
  Read dependencies.txt and install the listed dependencies. If they are not labeled "pip", get them through your system's package manager. Alternatively, install via the requirements.txt file. This is not guaranteed to be completely up to date however.
</p>
<p>
  Supply a "environment.py" that declares the following constants<br>
  <strong>
    WED_FROG # File path of picture of Wednesday frog<br>
    PROFILE_IMG # File path of profile image<br>
    # The remaining declarations are for gag functions and are not important<br>
    CHRISTMAS_1 # File path to Last Christmas audio file version 1<br>
    CHRISTMAS_2 # File path to Last Christmas audio file version 2<br>
    CHRISTMAS_3 # File path to Last Christmas audio file version 3<br>
  </strong>
</p>
<p>
  Additionally, supply the following in a .env file<br>
  <strong>
    WOLFRAM_TOKEN # User token for Wolfram Alpha API<br>
    BOT_TOKEN # Discord bot token<br>
  </strong>
</p>
<h3>Usage</h3>
<p>
  Start the bot by executing <code>Bot.py</code><br>
  By default, the command prefix is <code>></code><br>
  To get the list of default commands, type <code>>commands</code> in chat.<br>
  To get the list of music commands, type <code>>commands music</code> in chat.<br>
</p>
