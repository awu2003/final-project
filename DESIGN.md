# Design Document
This file should discuss how you implemented your project and why you made the design decisions you did, both technical and ethical. Your design document as a whole should be at least several paragraphs in length. Whereas your README.md is meant to be a user’s manual, consider your DESIGN.md your opportunity to give the staff a tour of your project underneath its hood.

## Technical Decisions

In this section, share and justify the technical decisions you made.

* What design challenge(s) did you run into while completing your project? How did you choose to address them and why?

### Implementing a file upload
One design challenge was implementing a file upload for the "Add image" feature. We were unfamiliar with the code syntax, so we needed to adapt existing code to implement the upload feature. This solution was efficient and allowed us to learn new syntax.

### Processing YouTube and Spotify URLs
Another challenge was rendering the YouTube and Spotify elements for a user's homepage. The URL for a YouTube video, for example, is different from the source code URL. We needed to partition the original URL to get the video's ID and then write code in the html to format the URL correctly so that video or song showed up on the user's homepage. We choose this solution because it was especially helpful for rendering the Spotify elements, since it allowed us to process any Spotify element, whether it's a playlist, song, or album.

* Was there a feature in your project you could have implemented in multiple ways? Which way did you choose, and why?

### Choosing languages
For the "Add design" feature, which allows the user to change the style of their website, including background color, we implemented it using Python and CSS. We could've used JavaScript, but we didn't want to have too many different languages in our code, since the other segments were implemented using Python. 

* If you used a new technology, what did you learn about this new technology? Did this technology prove to be the right tool?

### Git
We learned how to use Git so that we can seamlessly share code with each other. It proved to be a super useful tool for our project, since it allowed us to work on separate devices and merge code at certain touchpoints for the most updated version of our project. 

## Ethical Decisions

### What motivated you to complete this project? What features did you want to create and why?
We came across some really cool projects when looking for inspiration, and we wanted to create a website that was fun, useful, and accessible as well. We were inspired by platforms such as Squarespace and base our project on a similar concept. Users don't need to pay or subscribe to create a personalized website, and perhaps using our website will help them discover a new interest. 

We wanted to allow the user to include basic elements to their homepage, such as text, image, and videos, and to delete/move up/move down elements. This grants the user more freedom to personalize their site. We also wanted to allow the user to add friends and view their websites. This feature allows our website to be more interactive. 


### Who are the intended users of your project? What do they want, need, or value?
You should consider your project's users to be those who interact _directly_ with your project, as well as those who might interact with it _indirectly_, through others' use of your project.

Beyond the members of CS50, anyone can use our website! The user plays a direct role by using our features to create their website, and an indirect role when another user looks up their website. 

### How does your project's impact on users change as the project scales up? 
You might choose one of the following questions to reflect on:
* How could one of your project's features be misused?
* Are there any types of users who might have difficulty using your project?
* If your project becomes widely adopted, are there social concerns you might anticipate?

Because our project does not have a privacy feature, which would allow users to set their website to private, this means that any information that a user has on their website can be viewed by others. Without this privacy feature, we would encourage users not to include personal or sensitive information. 

Because some images might not have alt text, our project is not accessible for those who are visually impaired. This is something we would develop in future versions of the project.

Another concern is that certain uploaded Spotify songs or YouTube video might not be age-appropriate, so we would need to prevent young users from being able to view websites that have that content. For example, we would create a filter for user websites that include Spotify songs with an "Explicit" tag and YouTube videos that are not age-appropriate. 