<a id="readme-top"></a>



<!-- PROJECT SHIELDS -->
<div align="center">
  
  [![Contributors][contributors-shield]][contributors-url]
  [![Forks][forks-shield]][forks-url]
  [![Stargazers][stars-shield]][stars-url]
  [![Issues][issues-shield]][issues-url]
  [![MIT License][license-shield]][license-url]
  
</div>



<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/SuperDumbTM/rpi-paper-eta">
    <img src="https://github.com/user-attachments/assets/89d2baf0-205e-4ee8-8d28-2b2743ec5fb1" alt="Logo" width="80" height="80">
  </a>

  <h3 align="center">rpi-paper-eta</h3>

  <p align="center">
    Display ETAs with Raspberry Pi and E-paper with a comprehensive web management interface.
    <br />
    <br />
    <a href="https://github.com/SuperDumbTM/rpi-paper-eta/issues/new?labels=bug&template=bug-report---.md">Report Bug</a>
    ·
    <a href="https://github.com/SuperDumbTM/rpi-paper-eta/issues/new?labels=enhancement&template=feature-request---.md">Request Feature</a>
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

<p align="center">
  <img src="https://github.com/SuperDumbTM/rpi-paper-eta/assets/71750702/df5b37b3-30d3-4504-87cb-6586f41e53db" width="70%">
<p align="right">

This is a ETA display hardware gadget that provide ETA information for various transport within Hong Kong using a Raspberry Pi and a E-paper display.

Unlike most of the similar project, minimal setup is required without any of the configuration file modification, command entering or steep learning curve.
Most of the configuration can be done via a web management interface.

The data source of ETAs are [DATA.GOV.HK](https://data.gov.hk/en/).

<p align="right">(<a href="#readme-top">back to top</a>)</p>



### Built With

* [<img src="https://img.shields.io/badge/Alpine.js-77c1d2?style=for-the-badge&logo=Alpine.js&logoColor=white">](https://alpinejs.dev/)
* [<img src="https://img.shields.io/badge/bootstrap-7532fa?style=for-the-badge&logo=bootstrap&logoColor=white">](https://getbootstrap.com/)
* [<img src="https://img.shields.io/badge/flask-1b6d74?style=for-the-badge&logo=flask&logoColor=white">](https://flask.palletsprojects.com/)
* [<img src="https://img.shields.io/badge/htmx-3d72d7?style=for-the-badge&logo=htmx&logoColor=white">](https://htmx.org/)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->
## Getting Started

This is an example of how you may give instructions on setting up your project locally.
To get a local copy up and running follow these simple example steps.

### Prerequisites

* Python >= 3.10

Dependening on the E-paper display you are using, the required dependency will be different.
Please refer to the instruction from your display manufacturer.

* [Waveshare](https://www.waveshare.com/wiki/Main_Page#e-Paper)

### Installation

#### Setup

1. Clone the repo
   ```sh
   git clone https://github.com/SuperDumbTM/rpi-paper-eta.git
   ```
2. Install Pip packages
   ```sh
   pip install -r requirments.txt
   ```

#### Deploy

* Development
   ```sh
   flask run
   ```
* Production
   ```sh
   gunicorn
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
## Usage

### Web Management Interface

  - Route Bookmarking
  <img src="https://github.com/SuperDumbTM/rpi-paper-eta/assets/71750702/3790c860-9d54-4c61-b3fc-4c309498e631" width="65%">

  - Display Refresh Scheduling
  <img src="https://github.com/SuperDumbTM/rpi-paper-eta/assets/71750702/a556b64e-1cd4-4602-9b73-d3c348320d8a" width="65%">

### Customisation

Some of the default behaviour or storage path can be altered with a .env file (recommanded) or OS environment variable.
The setting is intended not to be able to configure via the web interface.

The details is as follow:

| **Variable**            	| **Description**                                                                                	|
|-------------------------	|------------------------------------------------------------------------------------------------	|
| BABEL_DEFAULT_LOCALE    	| A local code for the default displaying language of the CMS.                                   	|
| BABEL_DEFAULT_TIMEZO    	| A local code for the default time zone of the CMS (only used for   translation-related needs). 	|
| DIR_STORAGE             	| The directory name for the CMS to store the data (cache, logs, temporary   files) into.        	|
| DIR_SCREEN_DUMP         	| The directory name for the CMS to store the screen dump images.                                	|
| DIR_LOG                  	| The directory name for the CMS to store logs.                                                 	|
| SECRET_KEY              	| The key for the CMS to sing for security related needs such as session   cookie                	|

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/SuperDumbTM/rpi-paper-eta.svg?style=for-the-badge
[contributors-url]: https://github.com/SuperDumbTM/rpi-paper-eta/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/SuperDumbTM/rpi-paper-eta.svg?style=for-the-badge
[forks-url]: https://github.com/SuperDumbTM/rpi-paper-eta/network/members
[stars-shield]: https://img.shields.io/github/stars/SuperDumbTM/rpi-paper-eta.svg?style=for-the-badge
[stars-url]: https://github.com/SuperDumbTM/rpi-paper-eta/stargazers
[issues-shield]: https://img.shields.io/github/issues/SuperDumbTM/rpi-paper-eta.svg?style=for-the-badge
[issues-url]: https://github.com/SuperDumbTM/rpi-paper-eta/issues
[license-shield]: https://img.shields.io/github/license/SuperDumbTM/rpi-paper-eta.svg?style=for-the-badge
[license-url]: https://github.com/SuperDumbTM/rpi-paper-eta/blob/master/LICENSE.txt
