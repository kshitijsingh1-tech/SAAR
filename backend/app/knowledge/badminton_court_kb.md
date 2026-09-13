# Badminton Court Geometry & Tactical Spatial Grid Knowledge Base

## 1. BWF Standard Court Dimensions & Boundaries
According to the Badminton World Federation (BWF) Laws of Badminton:
- **Total Court Dimensions**: $13.40\text{ m}$ (44.0 ft) in length by $6.10\text{ m}$ (20.0 ft) in total width for doubles play.
- **Singles Court Width**: $5.18\text{ m}$ (17.0 ft), utilizing the inner lateral boundary lines ($0.46\text{ m}$ inward from each outer doubles sideline).
- **Net Height**: $1.55\text{ m}$ (5 ft 1 in) at the outer doubles boundary lines and $1.524\text{ m}$ (5 ft 0 in) at the center of the court.
- **Short Service Line**: Positioned $1.98\text{ m}$ (6 ft 6 in) from the net on each side.
- **Doubles Long Service Line**: Positioned $0.76\text{ m}$ (2 ft 6 in) inside the rear outer baseline.
- **Center Line**: Divides the left and right service courts from the short service line to the rear baseline at exactly $x = 3.05\text{ m}$.

## 2. Nine-Zone Tactical Court Grid (Section 10 Reference)
For spatial tracking, tactical distribution analysis, and region occupancy quantification, the court half is partitioned into a standardized $3 \times 3$ spatial grid (9 discrete zones):
1. **Forecourt Left (Net / Backhand)**: Net to short service line ($0.0\text{m} - 1.98\text{m}$ from net), $x \in [0.0\text{m}, 2.03\text{m}]$.
2. **Forecourt Center (T-Junction)**: Net to short service line, $x \in [2.03\text{m}, 4.07\text{m}]$.
3. **Forecourt Right (Net / Forehand)**: Net to short service line, $x \in [4.07\text{m}, 6.10\text{m}]$.
4. **Midcourt Left**: Short service line to midcourt transition ($1.98\text{m} - 4.70\text{m}$), $x \in [0.0\text{m}, 2.03\text{m}]$.
5. **Midcourt Center (Base Position)**: Optimal recovery centroid for singles base ($x \approx 3.05\text{m}, y \approx 3.5\text{m}-4.0\text{m}$).
6. **Midcourt Right**: Short service line to midcourt transition, $x \in [4.07\text{m}, 6.10\text{m}]$.
7. **Rearcourt Left (Backhand Corner / Overhead)**: Rear boundary zone ($4.70\text{m} - 6.70\text{m}$ from net), $x \in [0.0\text{m}, 2.03\text{m}]$.
8. **Rearcourt Center**: Rear boundary zone, $x \in [2.03\text{m}, 4.07\text{m}]$.
9. **Rearcourt Right (Forehand Rear Corner)**: Rear boundary zone, $x \in [4.07\text{m}, 6.10\text{m}]$.

## 3. Planar Homography & Camera Perspective Scaling
Transforming pixel image coordinates $(u, v)$ into metric court coordinates $(X, Y)$ requires a verified 4-point planar perspective transformation:
$$\begin{bmatrix} x' \\ y' \\ w \end{bmatrix} = \mathbf{H} \begin{bmatrix} u \\ v \\ 1 \end{bmatrix}, \quad X = \frac{x'}{w}, \quad Y = \frac{y'}{w}$$
- **Planar Coplanarity Requirement**: Homography strictly assumes all tracked player positions lie on the flat playing surface ($Z = 0$). Hip/pelvis midpoint tracking acts as an optical planar proxy.
- **Strict Degradation Rule**: If corner detection confidence is insufficient or perspective lines are occluded, physical spatial metrics (distance in meters, coverage area in $\text{m}^2$, region percentages) must degrade to unavailable rather than generating distorted approximations.
