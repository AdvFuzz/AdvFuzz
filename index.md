In this work, we propose the concept of adversarial NPC vehicles and introduce AdvFuzz, a novel simulation testing approach, to generate adversarial scenarios on main lanes (e.g., urban roads and highways). AdvFuzz allows NPC vehicles to dynamically interact with the EGO vehicle and regulates the behaviors of NPC vehicles, finding more violation scenarios caused by the EGO vehicle more quickly. We compare AdvFuzz with a random approach and three state-of-the-art scenario-based testing approaches. Our experiments demonstrate that AdvFuzz can generate 198.34% more violation scenarios compared to the other four approaches in 12 hours and increase the proportion of violations caused by the EGO vehicle to 87.04%, which is more than 7 times that of other approaches. Additionally, AdvFuzz is at least 92.21% faster in finding one violation caused by the EGO vehicle than that of the other approaches.

<!-- 补一句code代码点击这里查看 -->
The paper has been submitted to FSE 2025.

**For more details, see the code at [AdvFuzz GitHub Repository](https://github.com/AdvFuzz).**

## Overview
![Overview Image](/img/Overview_00.png)


## Waypoints Generation and Speed Planning

**LEFT_CHANGE maneuver**

<table>
  <tr>
    <td><img src="img/ST_graph1.png" alt="Graph 1" style="width:100%; max-width:500px; min-width:300px;"></td>
    <td><img src="img/ST_graph2.png" alt="Graph 2" style="width:100%; max-width:500px; min-width:300px;"></td>
  </tr>
</table>

**Description:** When the EGO vehicle is positioned to the left-rear of the NPC vehicle, the adversarial NPC vehicle initially proceeds straight before transitioning into the lane change. The trajectory waypoints are generated using Bézier curves to ensure a smooth path transition. Speed planning is then strategically crafted based on the EGO vehicle’s current speed and projected interactions, as depicted in the s-t graph, to anticipate and plan for potential collision points.

**Right_CHANGE maneuver** is similar to the LEFT_CHANGE maneuver, with the NPC vehicle transitioning from the right lane to the left lane.

**ACCELERATION_STRAIGHT maneuver**

<table>
  <tr>
    <td><img src="img/ST_graph6.png" alt="Acceleration Graph" style="width:100%; max-width:500px; min-width:300px;"></td>
    <td><img src="img/ST_graph3_00.png" alt="Speed Planning Graph" style="width:100%; max-width:500px; min-width:300px;"></td>
  </tr>
</table>

**Description:** When the EGO vehicle is positioned in the front-left, the adversarial NPC vehicle accelerates to overtake the EGO vehicle. As depicted in the right graph, at the moment t<sub>0</sub>, the NPC vehicle successfully overtakes the EGO vehicle.

**DECELERATION_STRAIGHT maneuver**

<table>
  <tr>
    <td><img src="img/ST_graph5.png" alt="Deceleration Graph" style="width:100%; max-width:500px; min-width:300px;"></td>
    <td><img src="img/ST_graph2_00.png" alt="Speed Control Graph" style="width:100%; max-width:500px; min-width:300px;"></td>
  </tr>
</table>

**Description:** When the EGO vehicle is behind the NPC vehicle, the adversarial NPC vehicle decelerates to simulate a rear-end collision scenario. The right graph shows the speed planning strategy for the NPC vehicle to ensure a collision with the EGO vehicle.

**KEEP_SPEED maneuver**

<table>
  <tr>
    <td><img src="img/ST_graph7_00.png" alt="Keep Speed Graph" style="width:100%; max-width:500px; min-width:300px;"></td>
    <td><img src="img/ST_graph8_00.png" alt="Speed Planning Graph" style="width:100%; max-width:500px; min-width:300px;"></td>
  </tr>
</table>

**Description:** When the EGO vehicle is in front of the NPC vehicle, the adversarial NPC vehicle maintains a constant speed to avoid a collision. 



## Examples of Generated Scenarios
Here are some dynamically generated scenarios using AdvFuzz, showcasing how the EGO vehicle interacts with adversarial NPC vehicles:

| ![type1](img/type1.gif) | ![type2](img/type2.gif) |
|:------------------------:|:------------------------:|
| Type 1: EGO rear-ends NPC changing lanes | Type 2: EGO hits the side of a NPC |
| ![type3](img/type3.gif) | ![type4](img/type4.gif) |
| Type 3: EGO collides with an NPC | Type 4: EGO hits the rear of an NPC |
| ![type5](img/type5.gif) | ![type6](img/type6.gif) |
| Type 5: EGO hits other NPCs stuck on lane | Type 6: EGO changes across yellow line |
| ![type7](img/type7.gif) | ![type8](img/type8.gif) |
| Type 7: EGO hits the yellow line | Type 8: EGO fails to plan trajectory |
| ![type9](img/type9.gif) | ![type10](img/type10.gif) |
| Type 9: EGO hits the rear of an NPC | Type 10: EGO side-collides with an NPC |
| ![type11](img/type11.gif) | ![type12](img/type12.gif) |
| Type 11: EGO hits the side of an NPC | Type 12: EGO collides with an NPC |
| ![type13](img/type13.gif) | ![type14](img/type14.gif) |
| Type 13: EGO collides with two NPC vehicles. | Type 14: EGO fails to plan trajectory |

**Note:** To replicate specific experimental scenarios in this documentation, refer to the data stored in the `/records` folder.

