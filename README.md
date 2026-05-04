n-body star cluster
![Brute Force](brute_force.gif)

Small Python simulation of a few hundred gravitating bodies. I built the first version over a weekend, and have been chipping away at it since — most recently rewriting the force calculation to use Barnes-Hut so it doesn't grind to a halt with bigger clusters.
## Comparison

| Brute Force O(n²) | Barnes-Hut O(n log n) |
|---|---|
| ![Brute Force](brute_force.gif) | ![Barnes-Hut](simulation.gif) |

Same 500 stars, same initial conditions. Brute force runs at 3-4 FPS, Barnes-Hut at 7-8 FPS — roughly 2x faster, and the gap widens as star count increases.

## What it does
A few hundred star-like point masses get scattered with random velocities inside a roughly spherical volume, then left alone. Newtonian gravity does the rest. Over time you get the things you'd expect from a real cluster — close pairs forming, looser stars wandering off, occasional slingshots when something passes too close to a tight binary. Nothing fancy. But it's genuinely satisfying to watch emerge from a few hundred lines of code and the inverse-square law.
The Barnes-Hut bit
The original version was a straightforward double loop: for every body, sum the gravitational pull from every other body. That's O(n²), and it shows. With 500 bodies the framerate was crawling.
Barnes-Hut replaces that loop with a quadtree. The simulation space gets recursively divided into quadrants, and each internal node stores the centre of mass of everything inside it. When computing the force on a body, you walk the tree from the root: if a node is "far enough away" relative to its size (controlled by a threshold called theta), you treat the whole node as one point mass at its centre of mass. Otherwise you recurse into its children.
This drops the complexity to O(n log n). Concretely, the version I have now runs ~500 bodies smoothly where the brute-force version started chugging around 150.
A few things tripped me up while building it:

Tree construction is the easy part. The centre-of-mass aggregation is the annoying part. It has to happen after all bodies are inserted, not as you go, otherwise you get stale values that quietly poison everything downstream.
theta = 0 is just brute-force again. Useful as a sanity check, if your Barnes-Hut output with theta = 0 doesn't match your O(n²) output, something's wrong with the tree, not the threshold.
Particles drifting outside the root bounds. If the simulation space expands faster than the root quadtree boundary, things break silently. I currently rebuild the tree from scratch each frame and size it to fit all bodies. Wasteful, but it works, and the rebuild is cheap compared to the force calc.

I cross-checked the Barnes-Hut version against the original brute-force one for small N — energies and trajectories match within the tolerance you'd expect from a theta-based approximation.
Running it
bashgit clone https://github.com/mirlan0705/n-body-star-cluster
cd n-body-star-cluster
pip install -r requirements.txt
python main.py
Tested on Python 3.11. Pygame and NumPy are the only real dependencies.
A few things to tweak in config.py:

N_BODIES — number of stars. Try 100 first, then push it.
THETA — Barnes-Hut threshold. ~0.5 is the usual default. Lower = more accurate, slower. Higher = faster, sloppier.
DT — timestep. Smaller is more stable, but linearly slower.

What I learned / what's next
Honestly the most useful thing this project has taught me has very little to do with physics. It's that "the algorithm" and "the implementation" are two different problems, and you can spend a week debugging the second without realising. I knew what an O(n²) loop was before I started. Writing one that didn't accidentally compare objects by identity instead of equality, or update positions and velocities in the wrong order, was a different skill — and one I needed two rewrites to actually internalise.
Things I want to come back to:

A proper integrator (leapfrog or kick-drift-kick) instead of the basic Euler step. Energy drift is noticeable over long runs.
Octree instead of quadtree, for proper 3D.
Softening parameter tuning, so close pairs don't fling each other to infinity.

Eventually this feeds into a Schwarzschild geodesic / black hole rendering project. Barnes-Hut won't be directly useful there, but the muscle memory for spatial data structures and numerical stability will be.
