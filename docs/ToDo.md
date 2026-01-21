1. Add a prioritized knowledgebase. When generating lessons, the app will first refer to this list of websites and documents.

https://docs.blender.org/manual/en/latest/, https://studio.blender.org/training/, https://mastodon.social/tags/b3d

2. Add capability in Preference for user to specify resource targets, along with broader "Internet Access"

3. In the UI, after a lesson is generated include a toggle to view the sources referenced.

Q. Question: can we adjust Codex VSCode settings to run specifically on my local GPU for faster processing? Or other recommendations for performance enhancement? Is it faster to run in a custom cloud environment?

4. ..

## Recommended Order (viability first)

### MVP: Core lesson flow and persistence

1. ~~Improve lesson output, incorporate Next and Previous step controls~~
2. ~~Save/Export chat text as a lesson file~~
3. Learning Paths can be saved and continued on next Blender session

### Phase 2: Guidance UX

4. Highlight UI tools for interactive step-by-step tutorial
5. Expand capabilities for Chiron to suggest tutorials and exercises
6. Capability for Chiron to generate custom Learning Paths per student request

### Phase 3: Audio

7. Add TTS functionality for Chiron to guide students audibly

## Dependencies / Notes

- Step controls should define a lesson state model (step index, completion, back/forward).
- Persistence should include schema versioning for saved lessons/paths.
- UI highlighting likely needs context-aware node editor targeting and robust error handling.
- TTS requires platform/permission decisions and a fallback for offline use.

## Once stable, expand to additional tools

1. Physics
2. Animation
3. Rigging
4. etc.

## Additional Tracking (mixed dev + ops)

1. Build beginner intro, launch with Geometry Nodes, iterate
2. Research Vertex AI / other providers for trained LLM options, off-line
3. Heavy negative testing, cross-platform validation
4. Set up CI/CD, Playwright, portfolio-ready pipeline
5. Reserve Chiron YouTube channel
6. Release in packages and create a ChironPHD
7. Breakout expand panel/frame
8. User-selectable skill level for tutorial detail
9. Prompt/Instruction library
10. Upload reference image
11. Notifications/reminders for daily lessons
12. User community: Discord + web page
13. Socials: YouTube, TikTok, X, Instagram
14. Set up Gumroad
15. Tiered versions LT/GT/OT/XT (pricing + feature matrix)
16. ChironLT: $8 suggested, low LLM API, no TTS/GT features
17. ChironGT: $18 required
18. ChironOT: $3 per package
19. ChironXT: $24 lifetime for all updates/add-ons
20. Avoid nickel-and-diming the students. Be Gracious.
21. Set up static repo
22. ID verified on Blender
23. Demo content: weekly long-form, daily short-form
24. Recreate popular YouTube tutorials
25. Change GWorkspace account to remotelyamused admin
26. Clean up GitHub or start RemotelyAmused account
27. Plan advanced/boutique lessons for add-on collabs (Gaussian splat, GIS, Blosm, LEGO, etc.)
28. Explore LDraw/MecaBricks/BrickLinkStudio add-on support
29. "Creativity in the Loop"
30. VoxCPM - https://go.juliangoldie.com/strategy-...
31. Offline LLM
32. Vertex AI

Ah, yes. It looks good as is. Whatever you did worked well.

Let's proceed,

Item 3.

a. I'm envisioning each section of the User Manual as a "Learning Path" of sorts.

b. For this first iteration, we are still focused on Geometry Nodes.

c. When the user enables Chiron in Preferences, there needs to be a picklist of "Learning Paths", structured just the same as the file tree of the User Manual.

d. Add "Modeling > Geometry Nodes " to the "Learning Paths" selection

e. Any activated Learning Path will be available in the UI tab of Chiron

f. User can then select "Geometry Nodes" from the Chiron tab, and Chiron present a few options based on the sub-folders, and will generate a tutorial based on the user selected topic

g. Inlcude a lesson tracking capability, so avoid repeat lesson content
