# EXPENSES TRACKER
### Video Demo: https://youtu.be/nRXIPOBceuE
### Description:
The Expenses tracker is an easy-to-access platform users can use to keep track of their monthly spendings, set budgets and make smarter financial decisions. The website was mainly designed with goal of reducing user resistance as much as possible in order to increase the likelihood of users forming a proper habit of tracking their expenses.

Users can __Add, Delete, Update,__ and monitor their expenses with ease through various features available in the website.

The website was developed using cs50.dev, a cloud based development environment, which allowed me to develop the project seamlessly across multiple devices and locations depending on my convenience.

The project is mainly built using Python with the Flask Framework. It also uses various other languages such as JavaScript, SQL, Flask-Login, Jinja and frameworks like BootStrap, Charts.js and Flatpickr

All the html files contain code which work together with BOOTSTRAP, FLASK AND CSS to improve the UX of the website.

#### HTML files:
- **add.html** - Allows the user to add an expense and submit it along with its respective category, amount and description.
- **apology.html** - Inspired by the cs50 week 9 assignment. Its main purpose is to help users identify their error and prompt rectification in a clean and user-friendly way.
- **budget.html** - Allows users to set budgets for various categories and update them in the future. The highlight of the page is the progress bar chart that displays users' spending relative to their set budgets, enabling them to monitor their remaining budget and pay attention to any overspending.
- **history.html** - Enables the user to track their past expenses with displayed timestamps.
- **index.html** - The main page of the website. It has various features such edit, delete, sort and filter expenses of any kind, giving the users maximum control over their entries.
- **layout.html** - Contains the template for all the other html files as well the source code for the other frameworks used (bootstrap and charts.js).
- **login.html** - Enables the users to gain access to their accounts.
- **proteinperdollar.html** - permits the user to determine the most cost-effective protein meals, enabling them to meet their fitness goals while living on a budget
- **register.html** - Allows new users to create an account.
- **stats.html** - Allows users to visualise their spendings using graphs such as line graphs, bar charts as well as doughnut charts for easier interpretation.

#### app.py:
This file serves as the core backend of the application. It handles routing, user authentication, database interactions and contains main application logic. It also connects the frontend templates to the expenses.db database using flask.

#### Sql database (Expenses.db):
Expenses.db mainly consists of 4 tables, each of which serves a different purpose. They are:
- **Users** - Stores all the information related to the users such as their username, their hashed password and their email addresses. This the table that enables user authentication.
- **Expenses** - Stores all user expenses entries such as they amount they spent, the category is expense pertains to, description related to their expense are stored in this table.
- **Protein** - This table was mainly used for the protein per dollar page. It stores the product information given by the user as well as the final result of the calculations made in the app.py file.
- **Budget** - Stores information regarding the budgets set for each category by the user. Being constantly updated, the table also stores the month and year to ensure accurate tracking and information retrieval.


#### Limitations:
1. I did not implement a forgot password feature. Proper implementation requires sending a verification link to the users' email ids to ensure secure identity verification. This is a lot more complicated than I thought it was as it requires a lot of external services and integrations and is honestly beyond my skill level.
2. I decided to go with the most popular preset categories instead of allowing the users to make their own. While this is not the most accurate way to go about it, it definitely ensures consistency and also removes the hassle of accounting for human errors (for example, a user may refer to a certain category as "entertainment" in one instance and refer to the same category as "recreation" some other time). However this comes at a cost of limiting the user's flexibility to choose their categories. An improvement could be to add a section in which the users can add/edit/delete their categories which are then standardized across the website.
3. My initial plan was to create an app fir highly accessible daily usage. However being a student with numerous financial constraints, my current plan is to make a highly responsive website optimised well for smart phone and create a shortcut for it instead. This creates a pseudo-app experience without additional costs. This is still a work in progress.
