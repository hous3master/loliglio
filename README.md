![Loliglio web page banner](https://2640050380-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2Fbu0mjMsSISfI64girFHC%2Fuploads%2FG1C5v7BsnxAxB13665Xl%2FNew%20Project%20(7).png?alt=media&token=c1c5a408-9834-4178-a89a-31a6b393c9e2)

# Loliglio
## Riot API made easy!
Loliglio allows you to extract data from the Riot API easily for your app development. Loliglio Framework is also intuitive and free.
## Capabilities
- Ordered access to APIs through classes and methods. For example one can access the mastery information of a summoner via:
- ChampionMastery.by_summoner(regionId, encryptedSummonerId)
- Support for both Riot and Comunnity Dragon API. Facilitating the joint work of official information and information provided by the League of Legends community.
- Support for V3, V4 and V5 APIs.
- Region and cluster servers, as well as queues, tiers and divisions are identified by Loliglio's own IDs instead of text. This facilitates their use, avoids errors due to the use of text strings, and above all, makes the storage and analysis of games through a database more efficient.
- Full access to all information available for and through the Riot API development key.
- Full free access to Community Dragon information
- 10 different classes, related by output data
- 40 different types of function queries, each with unique customization.
- Does not require the installation of additional libraries, since it uses only those present in the Standard Python Library.
- Facilitates error handling when querying an API.
- It has an internal rate limiter that prevents reaching the limit of available queries.
- In any case the limit of queries is reached. The library handles the error automatically to avoid possible bans.
- All outputs are JSON objects, and work just like a dictionary.

Check the detailed documentation here: https://conradofmf.gitbook.io/loliglio/

Loliglio is made by Conrado Moreno, contact me trough
- https://github.com/hous3master
- cfmorenofernandez@gmail.com
- https://www.linkedin.com/in/conrado-moreno-fern%C3%A1ndez-01a17220a/
