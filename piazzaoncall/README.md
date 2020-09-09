# Piazza-Oncall 

## Description 
Piazza-Oncall monitors piazza and pings the staff Slack to help with unanswered questions. It assigns a staff member to each question (with individual staff members for each followup) and sends out a daily reminder for all unresolved questions and followups. 

## Setup
All packages are detailed in requirements.txt. Include a .csv file named staff_roster.csv in the program directory. The staff roster should minimally contain `email`, `name`, and `Weight` columns; extraneous columns will be ignored. Name/email will indicate the staff member to tag in slack while the `Weight` indicates their probability of being selected for a random post/followup — note that `Weight` is capitalized. 

## High Priority Messages

If a question remains unresolved for some customizable (default: 3) days, the reminder includes `@channel` to encourage a faster response to the post or followup. A post's age is determined by its date of creation, while a followup's age is determined by its last nested comment. For example, a 5-day old (unresolved) followup with a 3-hour old reply would  not be marked as high priority, since it would be dated at 3-hours old. However, it still would be included in the regular reminders since it's still marked unresolved. 

## Assign Staff Members 
The syntax `oncall: <email_username>` can be used to assign specific staff members to a post. For example, `oncall: oski` in the body of the piazza post would assign the staff member with oski@berkeley.edu to the post. Staff members assigned with the oncall syntax are responsible for the entire post, including any followups (no new staff members will be assigned to followups). 

Oncall can also be used to assign multiple staff members. For example, 

```
oncall: oski
oncall: gobears
```

in the body of the piazza post would assign the staff members with emails oski@berkeley.edu and gobears@berkeley.edu to the entire post, including any followups. 

## Exclude Posts
To prevent a staff member from being assigned to an unresolved post, use the syntax `oncall: ignore`. Ignore takes precedence over any other assignment. For example, 

```
oncall: oski
oncall: ignore
```

would result in no staff members being assigned to the post, even though oski was specified for assignment. 
