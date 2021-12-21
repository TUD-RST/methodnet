In the papers linked in the README file, we describe so called “output options“, which are make it possible to encode
branching decisions in methods in the static solution procedure. An example would be a test for controllability that
could either yield a controllable or uncontrollable system object, depending on the specifics given at runtime.

These output options were found to significantly complicate both path finding as well as the readility of the generated
solutioin procedure graph. It was also hard to make a case for their usefulness, as there was almost always just one
happy path, with all others either immediatel terminating or being redundant (and resulting from technicalities).
For this reason, output options were removed from the code and only the „happy“ options kept in the knowledge graph.

For future refence, a similar feature could be added by expanding the UI. If a user finds that a method doesn't succeed,
they could have the option to easily restart solution procedure path finding, with the “unhappy” serving as the new
starting point.