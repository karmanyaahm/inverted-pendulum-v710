

Summary of training options (whether we need fast compute on the robot (esp vs. rpi vs. jetson nano)):

Should be able to run on anything as long as we can transmit transitions to a computer that does the training. This may be slower because we are doing this offline but this should work. It also might be cool to look at some sim-to-real options but this seems difficult given that we don't have a proper simulation of the robot.

- Cheap inference
- Train while running on robot
- Sim
- episode