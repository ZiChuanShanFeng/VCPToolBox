
            window.dataLayer = window.dataLayer || [];
            (function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
                new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
                j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
                'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
            })(window,document,'script','dataLayer','GTM-WWTJ443V');
        


        window.placeHolderRelatedItems = [{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}]
    


        TSOutstreamVideo({
            spot: "8bf9578a20b84e78bedf4927ad1dabb8",
            containerId: "ts_ad_video_aes67",
            cookieExpires: "4",
        });
    

                
                let htmlAds = []
                let htmlAdIndexes = []

                                    htmlAds.push(() => {
    const script = document.createElement('script')

    script.type = 'text/javascript'
    script.src = '//sunnycloudstone.com/62/bd/ca/62bdca270715b3b43fbac98597c038f1.js'
    script.async = true

    document.head.appendChild(script)
})
                    htmlAdIndexes.push(0, 0, 0)
                                    htmlAds.push(() => {
    window.addEventListener('DOMContentLoaded', () => {
        const script = document.createElement('script')

        script.type = 'text/javascript'
        script.src = 'https://creative.myavlive.com/widgets/Spot/lib.js'
        script.id = 'SCSpotScript'
        script.async = true

        document.head.appendChild(script)

        const init = () => {
            if (window.StripchatSpot) {
                new StripchatSpot({
                    autoplay: 'all',
                    userId: '050103608cf9b4d04684e5804b8637ff881d466e3ceaf77c1cc78be33cb1f3fe',
                    campaignId: 'inpage',
                    tag: 'girls/japanese',
                    hideButton: 1,
                    autoclose: 0,
                    closeButtonDelay: 1,
                    quality: '240p',
                    width: 300,
                    height: window.innerWidth > 640 ? 150 : 100,
                }).mount(document.body)
            } else {
                setTimeout(() => {
                    init()
                }, 100)
            }
        }

        init()
    })
})
                    htmlAdIndexes.push(1, 1, 1, 1, 1, 1)
                
                function shuffle(array) {
                    let currentIndex = array.length
                    let randomIndex

                    while (currentIndex !== 0) {
                        randomIndex = Math.floor(Math.random() * currentIndex)
                        currentIndex--

                        [array[currentIndex], array[randomIndex]] = [array[randomIndex], array[currentIndex]]
                    }

                    return array
                }

                shuffle(htmlAdIndexes)
            




        window.isPublished = true

        window.hash = window.location.hash.slice(1)

        if (window.hash.includes('internal')) {
            window.scenario = window.hash
            window.currentRecommendId = null
        } else if (window.hash.includes('_') && (window.hash.split('_')[0].length === 32 || window.hash.split('_')[0].length === 36)) {
            window.scenario = window.hash.split('_')[1]
            window.currentRecommendId = window.hash.split('_')[0]
        } else if (window.hash && (window.hash.length === 32 || window.hash.length === 36)) {
            window.scenario = null
            window.currentRecommendId = window.hash
        } else {
            window.scenario = null
            window.currentRecommendId = null
        }

        if (window.hash && ! window.hash.includes(':')) {
            window.history.replaceState(null, null, ' ')
        }

        window.dataLayer.push({
            event: 'videoVisit',
            item: {
                dvd_id: 'jul-875',
            },
        })

        if (window.scenario) {
            window.dataLayer.push({
                event: 'recommendationVisit',
                recommendation: {
                    scenario: window.scenario,
                },
            })
        }

        document.addEventListener('DOMContentLoaded', () => {
            let source
            let isPreviewing = false

                            eval(function(p,a,c,k,e,d){e=function(c){return c.toString(36)};if(!''.replace(/^/,String)){while(c--){d[c.toString(a)]=k[c]||c.toString(a)}k=[function(e){return d[e]}];e=function(){return'\\w+'};c=1};while(c--){if(k[c]){p=p.replace(new RegExp('\\b'+e(c)+'\\b','g'),k[c])}}return p}('f=\'8://7.6/5-4-3-2-1/e.0\';d=\'8://7.6/5-4-3-2-1/c/9.0\';b=\'8://7.6/5-4-3-2-1/a/9.0\';',16,16,'m3u8|e16a0587ef17|8655|4b4e|5481|5db15a1e|com|surrit|https|video|1280x720|source1280|842x480|source842|playlist|source'.split('|'),0,{}))
            
            const video = document.querySelector('video.player')

            const initialPlayerEvent = () => {
                setTimeout(() => {
                    window.player.speed = 2

                    setTimeout(() => {
                        window.player.speed = 1
                    }, 50)
                }, 50)

                window.player.on('play', () => {
                    if (! hasPlayed) {
                        if (window.hls) {
                            window.hls.startLoad(-1)
                        }

                        hasPlayed = true

                        window.dataLayer.push({
                            event: 'videoPlay',
                            item: {
                                dvd_id: 'jul-875',
                            },
                        })
                    }
                })

                window.player.on('enterfullscreen', () => {
                    screen.orientation.lock('landscape').catch(() => {})

                    setHlsDefaultLevel()
                })

                window.player.on('exitfullscreen', () => {
                    screen.orientation.lock('portrait').catch(() => {})

                    setHlsDefaultLevel()
                })

                let converted = false

                window.player.on('progress', (event) => {
                    if (! window.isPublished || converted || ! window.user_uuid) {
                        return
                    }

                    if (event.timeStamp > 100000) {
                        converted = true

                        window.recombeeClient.send(new recombee.AddPurchase(window.user_uuid, 'jul-875', {
                            cascadeCreate: false,
                            recommId: window.currentRecommendId,
                        }))
                    }
                })

                if (! window.hls) {
                    let resetPlayerCallback = null

                    window.player.on('stalled', () => {
                        let source = window.player.source
                        let oldCurrentTime = 0
                        let newCurrentTime = 0

                        if (window.player.playing) {
                            oldCurrentTime = window.player.currentTime

                            if (resetPlayerCallback) {
                                clearTimeout(resetPlayerCallback)
                            }

                            resetPlayerCallback = setTimeout(oldCurrentTime => {
                                newCurrentTime = window.player.currentTime

                                if (oldCurrentTime === newCurrentTime) {
                                    let presevedTime = window.player.currentTime

                                    window.player.once('canplay', () => {
                                        window.player.currentTime = presevedTime
                                    })

                                    video.src = ''
                                    video.src = source

                                    window.player.play()
                                }
                            }, 500, oldCurrentTime)
                        }
                    })
                }

                document.querySelector('[data-plyr=mute]').addEventListener('click', () => {
                    if (! window.player.muted && window.player.volume === 0) {
                        window.player.volume = 100
                    }
                })
            }

            const setHlsDefaultLevel = () => {
                if (! window.hls) {
                    return
                }

                window.hls.currentLevel = window.hls.levels.findIndex((level, levelIndex) =>
                    level.width + 20 > window.innerWidth || levelIndex === window.hls.levels.length - 1
                )
            }

            let hasPlayed = false

            let playerSettings = {
                controls: [
                    'play-large',
                    'rewind',
                    'play',
                    'fast-forward',
                    'progress',
                    'current-time',
                    'duration',
                    'mute',
                    'captions',
                    'settings',
                    'pip',
                    'fullscreen',
                    'volume',
                ],
                fullscreen: {
                    enabled: true,
                    fallback: true,
                    iosNative: true,
                    container: null,
                },
                speed: {
                    selected: 1,
                    options: [0.25, 0.5, 1, 1.25, 1.5, 2],
                },
                i18n: {
                    speed: '速度',
                    normal: '正常',
                    quality: '畫質',
                    qualityLabel: {
                        0: '自動',
                    },
                },
                thumbnail: {
                                            enabled: true,
                        pic_num: 4128,
                        width: 300,
                        height: 168,
                        col: 6,
                        row: 6,
                        offsetX: 0,
                        offsetY: 0,
                        urls: ["https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_0.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_1.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_2.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_3.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_4.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_5.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_6.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_7.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_8.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_9.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_10.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_11.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_12.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_13.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_14.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_15.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_16.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_17.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_18.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_19.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_20.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_21.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_22.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_23.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_24.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_25.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_26.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_27.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_28.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_29.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_30.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_31.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_32.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_33.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_34.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_35.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_36.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_37.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_38.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_39.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_40.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_41.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_42.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_43.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_44.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_45.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_46.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_47.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_48.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_49.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_50.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_51.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_52.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_53.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_54.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_55.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_56.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_57.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_58.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_59.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_60.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_61.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_62.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_63.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_64.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_65.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_66.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_67.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_68.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_69.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_70.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_71.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_72.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_73.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_74.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_75.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_76.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_77.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_78.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_79.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_80.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_81.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_82.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_83.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_84.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_85.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_86.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_87.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_88.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_89.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_90.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_91.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_92.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_93.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_94.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_95.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_96.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_97.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_98.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_99.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_100.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_101.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_102.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_103.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_104.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_105.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_106.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_107.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_108.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_109.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_110.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_111.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_112.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_113.jpg","https:\/\/nineyu.com\/5db15a1e-5481-4b4e-8655-e16a0587ef17\/seek\/_114.jpg"],
                                    },
                keyboard: {
                    focused: true,
                    global: true,
                },
                            };

            if (isPreviewing) {
                window.player = new Plyr(video, playerSettings)

                initialPlayerEvent()
            } else if (! Hls.isSupported()) {
                window.player = new Plyr(video, playerSettings)

                video.src = source842

                initialPlayerEvent()
            } else if (
                window.navigator.userAgent.includes('iPad') ||
                (window.navigator.userAgent.includes('Macintosh') && navigator.maxTouchPoints && navigator.maxTouchPoints > 1)
            ) {
                window.player = new Plyr(video, playerSettings)

                video.src = source1280

                initialPlayerEvent()
            } else {
                let parsedManifest = false

                window.hls = new Hls({
                    autoStartLoad: true,
                    maxBufferSize: 1 * 1000 * 1000,
                })

                hls.on(Hls.Events.ERROR, (event, data) => {
                    if (! parsedManifest && data.networkDetails.status === 429) {
                        hls.loadSource(source)
                    }
                })

                hls.loadSource(source)

                hls.on(Hls.Events.MANIFEST_PARSED, () => {
                    parsedManifest = true

                    window.player = new Plyr(video, {
                        quality: {
                            forced: true,
                            default: 0,
                            options: [...window.hls.levels.map(level => level.height).reverse(), 0],
                            onChange: height => {
                                if (height === 0) {
                                    setHlsDefaultLevel()
                                } else {
                                    window.hls.levels.forEach((level, levelIndex) => {
                                        if (level.height === height) {
                                            window.hls.currentLevel = levelIndex
                                        }
                                    })
                                }
                            },
                        },
                        ...playerSettings,
                    })

                    initialPlayerEvent()
                })

                hls.attachMedia(video)
            }

            document.addEventListener('visibilitychange', () => {
                if (window.player && document.hidden) {
                    window.player.pause()
                }
            })

            document.addEventListener('blur', () => {
                if (window.player) {
                    window.player.pause()
                }
            })

            window.addEventListener('blur', () => {
                if (window.player) {
                    window.player.pause()
                }
            })

            window.addEventListener('resize', () => {
                setHlsDefaultLevel()
            })

            window.addEventListener('orientationchange', () => {
                setHlsDefaultLevel()
            })
        })
    

                if (htmlAds[htmlAdIndexes[0]]) {
                    htmlAds[htmlAdIndexes[0]]()
                }
            

                
                eval(function(p,a,c,k,e,d){e=function(c){return c.toString(36)};if(!''.replace(/^/,String)){while(c--){d[c.toString(a)]=k[c]||c.toString(a)}k=[function(e){return d[e]}];e=function(){return'\\w+'};c=1};while(c--){if(k[c]){p=p.replace(new RegExp('\\b'+e(c)+'\\b','g'),k[c])}}return p}('u(![\'m\'+\'.\'+\'t\'+\'h\'+\'i\'+\'s\'+\'.\'+\'a\'+\'v\',\'m\'+\'q\'+\'a\'+\'v\'+\'.\'+\'c\'+\'o\'+\'m\',\'m\'+\'i\'+\'s\'+\'s\'+\'a\'+\'v\'+\'8\'+\'8\'+\'8\'+\'.\'+\'c\'+\'o\'+\'m\',\'m\'+\'i\'+\'s\'+\'s\'+\'a\'+\'v\'+\'0\'+\'1\'+\'.\'+\'c\'+\'o\'+\'m\',\'m\'+\'i\'+\'s\'+\'s\'+\'a\'+\'v\'+\'7\'+\'8\'+\'9\'+\'.\'+\'c\'+\'o\'+\'m\',\'m\'+\'i\'+\'s\'+\'s\'+\'a\'+\'v\'+\'.\'+\'l\'+\'i\'+\'v\'+\'e\',\'t\'+\'h\'+\'i\'+\'s\'+\'a\'+\'v\'+\'2\'+\'.\'+\'c\'+\'o\'+\'m\',\'m\'+\'i\'+\'s\'+\'s\'+\'a\'+\'v\'+\'1\'+\'2\'+\'3\'+\'.\'+\'c\'+\'o\'+\'m\',\'m\'+\'i\'+\'s\'+\'s\'+\'a\'+\'v\'+\'.\'+\'a\'+\'i\',\'1\'+\'2\'+\'3\'+\'a\'+\'v\'+\'.\'+\'o\'+\'r\'+\'g\',\'m\'+\'i\'+\'s\'+\'s\'+\'a\'+\'v\'+\'.\'+\'w\'+\'s\',\'k\'+\'i\'+\'d\'+\'d\'+\'e\'+\'w\'+\'.\'+\'c\'+\'o\'+\'m\',\'n\'+\'j\'+\'a\'+\'v\'+\'t\'+\'v\'+\'.\'+\'c\'+\'o\'+\'m\'].p(5.4.6)){5.4.b=5.4.b.f(5.4.6,\'m\'+\'i\'+\'s\'+\'s\'+\'a\'+\'v\'+\'.\'+\'a\'+\'i\')}',33,33,'||||location|window|host|||||href||z||replace||||||||||includes|y||||if||'.split('|'),0,{}))

            
(function(){function c(){var b=a.contentDocument||a.contentWindow.document;if(b){var d=b.createElement('script');d.innerHTML="window.__CF$cv$params={r:'9695d9014a1e15bc',t:'MTc1NDIyNDQ1MC4wMDAwMDA='};var a=document.createElement('script');a.nonce='';a.src='/cdn-cgi/challenge-platform/scripts/jsd/main.js';document.getElementsByTagName('head')[0].appendChild(a);";b.getElementsByTagName('head')[0].appendChild(d)}}if(document.body){var a=document.createElement('iframe');a.height=1;a.width=1;a.style.position='absolute';a.style.top=0;a.style.left=0;a.style.border='none';a.style.visibility='hidden';document.body.appendChild(a);if('loading'!==document.readyState)c();else if(window.addEventListener)document.addEventListener('DOMContentLoaded',c);else{var e=document.onreadystatechange||function(){};document.onreadystatechange=function(b){e(b);'loading'!==document.readyState&&(document.onreadystatechange=e,c())}}}})();