# Using Freqtrade with Docker¶

This page explains how to run the bot with Docker. It is not meant to work out of the box. You'll still need to read through the documentation and understand how to properly configure it.

## Install Docker¶

Start by downloading and installing Docker / Docker Desktop for your platform:

- Mac
- Windows
- Linux

Docker compose install

Freqtrade documentation assumes the use of Docker desktop (or the docker compose plugin).While the docker-compose standalone installation still works, it will require changing alldocker composecommands fromdocker composetodocker-composeto work (e.g.docker compose up -dwill becomedocker-compose up -d).

`docker compose`
`docker compose`
`docker-compose`
`docker compose up -d`
`docker-compose up -d`

If you just installed docker on a windows system, make sure to reboot your system, otherwise you might encounter unexplainable Problems related to network connectivity to docker containers.

## Freqtrade with docker¶

Freqtrade provides an official Docker image onDockerhub, as well as adocker compose fileready for usage.

Note

- The following section assumes thatdockeris installed and available to the logged in user.
`docker`
- All below commands use relative directories and will have to be executed from the directory containing thedocker-compose.ymlfile.
`docker-compose.yml`

### Docker quick start¶

Create a new directory and place thedocker-compose filein this directory.

```
mkdir ft_userdata
cd ft_userdata/
# Download the docker-compose file from the repository
curl https://raw.githubusercontent.com/freqtrade/freqtrade/stable/docker-compose.yml -o docker-compose.yml

# Pull the freqtrade image
docker compose pull

# Create user directory structure
docker compose run --rm freqtrade create-userdir --userdir user_data

# Create configuration - Requires answering interactive questions
docker compose run --rm freqtrade new-config --config user_data/config.json
```

The above snippet creates a new directory calledft_userdata, downloads the latest compose file and pulls the freqtrade image.
The last 2 steps in the snippet create the directory withuser_data, as well as (interactively) the default configuration based on your selections.

`ft_userdata`
`user_data`

How to edit the bot configuration?

You can edit the configuration at any time, which is available asuser_data/config.json(within the directoryft_userdata) when using the above configuration.

`user_data/config.json`
`ft_userdata`

You can also change the both Strategy and commands by editing the command section of yourdocker-compose.ymlfile.

`docker-compose.yml`

#### Adding a custom strategy¶

- The configuration is now available asuser_data/config.json
`user_data/config.json`
- Copy a custom strategy to the directoryuser_data/strategies/
`user_data/strategies/`
- Add the Strategy' class name to thedocker-compose.ymlfile
`docker-compose.yml`

TheSampleStrategyis run by default.

`SampleStrategy`

SampleStrategyis just a demo!

`SampleStrategy`

TheSampleStrategyis there for your reference and give you ideas for your own strategy.
Please always backtest your strategy and use dry-run for some time before risking real money!
You will find more information about Strategy development in theStrategy documentation.

`SampleStrategy`

Once this is done, you're ready to launch the bot in trading mode (Dry-run or Live-trading, depending on your answer to the corresponding question you made above).

```
docker compose up -d
```

Default configuration

While the configuration generated will be mostly functional, you will still need to verify that all options correspond to what you want (like Pricing, pairlist, ...) before starting the bot.

#### Accessing the UI¶

If you've selected to enable FreqUI in thenew-configstep, you will have freqUI available at portlocalhost:8080.

`new-config`
`localhost:8080`

You can now access the UI by typing localhost:8080 in your browser.

If you're running on a VPS, you should consider using either a ssh tunnel, or setup a VPN (openVPN, wireguard) to connect to your bot.
This will ensure that freqUI is not directly exposed to the internet, which is not recommended for security reasons (freqUI does not support https out of the box).
Setup of these tools is not part of this tutorial, however many good tutorials can be found on the internet.
Please also read theAPI configuration with dockersection to learn more about this configuration.

#### Monitoring the bot¶

You can check for running instances withdocker compose ps.
This should list the servicefreqtradeasrunning. If that's not the case, best check the logs (see next point).

`docker compose ps`
`freqtrade`
`running`

#### Docker compose logs¶

Logs will be written to:user_data/logs/freqtrade.log.You can also check the latest log with the commanddocker compose logs -f.

`user_data/logs/freqtrade.log`
`docker compose logs -f`

#### Database¶

The database will be located at:user_data/tradesv3.sqlite

`user_data/tradesv3.sqlite`

#### Updating freqtrade with docker¶

Updating freqtrade when usingdockeris as simple as running the following 2 commands:

`docker`

```
# Download the latest image
docker compose pull
# Restart the image
docker compose up -d
```

This will first pull the latest image, and will then restart the container with the just pulled version.

Check the Changelog

You should always check the changelog for breaking changes / manual interventions required and make sure the bot starts correctly after the update.

### Editing the docker-compose file¶

Advanced users may edit the docker-compose file further to include all possible options or arguments.

All freqtrade arguments will be available by runningdocker compose run --rm freqtrade <command> <optional arguments>.

`docker compose run --rm freqtrade <command> <optional arguments>`

docker composefor trade commands

`docker compose`

Trade commands (freqtrade trade <...>) should not be ran viadocker compose run- but should usedocker compose up -dinstead.
This makes sure that the container is properly started (including port forwardings) and will make sure that the container will restart after a system reboot.
If you intend to use freqUI, please also ensure to adjust theconfiguration accordingly, otherwise the UI will not be available.

`freqtrade trade <...>`
`docker compose run`
`docker compose up -d`

docker compose run --rm

`docker compose run --rm`

Including--rmwill remove the container after completion, and is highly recommended for all modes except trading mode (running withfreqtrade tradecommand).

`--rm`
`freqtrade trade`

"docker compose run --rm" will require a compose file to be provided.
Some freqtrade commands that don't require authentication such aslist-pairscan be run with "docker run --rm" instead.For exampledocker run --rm freqtradeorg/freqtrade:stable list-pairs --exchange binance --quote BTC --print-json.This can be useful for fetching exchange information to add to yourconfig.jsonwithout affecting your running containers.

`docker compose run --rm`
`list-pairs`
`docker run --rm`
`docker run --rm freqtradeorg/freqtrade:stable list-pairs --exchange binance --quote BTC --print-json`
`config.json`

#### Example: Download data with docker¶

Download backtesting data for 5 days for the pair ETH/BTC and 1h timeframe from Binance. The data will be stored in the directoryuser_data/data/on the host.

`user_data/data/`

```
docker compose run --rm freqtrade download-data --pairs ETH/BTC --exchange binance --days 5 -t 1h
```

Head over to theData Downloading Documentationfor more details on downloading data.

#### Example: Backtest with docker¶

Run backtesting in docker-containers for SampleStrategy and specified timerange of historical data, on 5m timeframe:

```
docker compose run --rm freqtrade backtesting --config user_data/config.json --strategy SampleStrategy --timerange 20190801-20191001 -i 5m
```

Head over to theBacktesting Documentationto learn more.

### Additional dependencies with docker¶

If your strategy requires dependencies not included in the default image - it will be necessary to build the image on your host.
For this, please create a Dockerfile containing installation steps for the additional dependencies (have a look atdocker/Dockerfile.customfor an example).

You'll then also need to modify thedocker-compose.ymlfile and uncomment the build step, as well as rename the image to avoid naming collisions.

`docker-compose.yml`

```
image: freqtrade_custom
    build:
      context: .
      dockerfile: "./Dockerfile.<yourextension>"
```

You can then rundocker compose build --pullto build the docker image, and run it using the commands described above.

`docker compose build --pull`

### Plotting with docker¶

Commandsfreqtrade plot-profitandfreqtrade plot-dataframe(Documentation) are available by changing the image to*_plotin yourdocker-compose.ymlfile.
You can then use these commands as follows:

`freqtrade plot-profit`
`freqtrade plot-dataframe`
`*_plot`
`docker-compose.yml`

```
docker compose run --rm freqtrade plot-dataframe --strategy AwesomeStrategy -p BTC/ETH --timerange=20180801-20180805
```

The output will be stored in theuser_data/plotdirectory, and can be opened with any modern browser.

`user_data/plot`

### Data analysis using docker compose¶

Freqtrade provides a docker-compose file which starts up a jupyter lab server.
You can run this server using the following command:

```
docker compose -f docker/docker-compose-jupyter.yml up
```

This will create a docker-container running jupyter lab, which will be accessible usinghttps://127.0.0.1:8888/lab.
Please use the link that's printed in the console after startup for simplified login.

`https://127.0.0.1:8888/lab`

Since part of this image is built on your machine, it is recommended to rebuild the image from time to time to keep freqtrade (and dependencies) up-to-date.

```
docker compose -f docker/docker-compose-jupyter.yml build --no-cache
```

## Troubleshooting¶

### Docker on Windows¶

- Error:"Timestamp for this request is outside of the recvWindow."The market api requests require a synchronized clock but the time in the docker container shifts a bit over time into the past.
  To fix this issue temporarily you need to runwsl --shutdownand restart docker again (a popup on windows 10 will ask you to do so).
  A permanent solution is either to host the docker container on a linux host or restart the wsl from time to time with the scheduler.taskkill/IM"Docker Desktop.exe"/F
wsl--shutdown
start"""C:\Program Files\Docker\Docker\Docker Desktop.exe"

Error:"Timestamp for this request is outside of the recvWindow."The market api requests require a synchronized clock but the time in the docker container shifts a bit over time into the past.
  To fix this issue temporarily you need to runwsl --shutdownand restart docker again (a popup on windows 10 will ask you to do so).
  A permanent solution is either to host the docker container on a linux host or restart the wsl from time to time with the scheduler.

`"Timestamp for this request is outside of the recvWindow."`
`wsl --shutdown`

```
taskkill /IM "Docker Desktop.exe" /F
wsl --shutdown
start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
```

- Cannot connect to the API (Windows)If you're on windows and just installed Docker (desktop), make sure to reboot your System. Docker can have problems with network connectivity without a restart.
  You should obviously also make sure to have yoursettingsaccordingly.

Warning

Due to the above, we do not recommend the usage of docker on windows for production setups, but only for experimentation, datadownload and backtesting.
Best use a linux-VPS for running freqtrade reliably.