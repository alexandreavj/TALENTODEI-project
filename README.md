# TALENTODEI-project
Talento@DEI | Mind Reader: Using Biofeedback and AI to Predict Your Next Move

# TobbiDemo.java
This script provides tools for connecting to the Tobii 5L and extracting the gaze data to a text file, allowing to specify the sampling rate.

# empatica_raw_data.py
This script provides tools for extracting EDA and BVP values from Empatica EmbracePlus files, as well as processing them.

# eyetracker_connectio.py
This script provides tools for connecting to the Tobii 5L and extracting the gaze data with pupil diameter (requires a license).

# eyetracker_data.py
This script provides tools for processing the raw gaze data (obtained from running `TobiiDemo.java`).
Extract fixations and aggregates them (as well as the gaze data) by each card region.
FEATURES EXTRACTED:
- card with longest fixation
- card with longest visit
- card with more visits
- last card fixated

# GUI.py
Game interface and connection between the several scripts, assuring the data collection form the EyeTracker by socket communication, as well as the data processing in real time.

# OLD_eyetracker_data.py
This script provides tools for processing the raw gaze data (obtained from running `TobiiDemo.java`), exporting the data to several text files, as well as creating a visualization of the gaze data behaviour on screen.