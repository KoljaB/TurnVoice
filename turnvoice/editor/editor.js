let tracks = {};
let originalData = {};
const pixelsPerSecond = 100;
let track_width = 0;
let timeline_position = 0;
const track_height = 60;
let zIndexCounter = 100;
let loadedFileName = "";
const tracksContainer = document.getElementById('tracksContainer');
const timelineContainer = document.getElementById('currentTimeLine');
const cliOutput = document.getElementById('cliOutput');
const autoScroll = document.getElementById('chkAutoscroll');
file_name_edited_script = "edited_render_script.json"

function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        loadedFileName = file.name;
        const reader = new FileReader();
        reader.onload = function(e) {
            const content = e.target.result;
            const data = JSON.parse(content);
            processData(data);
        };
        reader.readAsText(file);
    }
}

// This function will process the data and create the tracks and blocks
function processData(data) {
    while (tracksContainer.firstChild) {
        tracksContainer.removeChild(tracksContainer.firstChild);
    }

    tracks = {};
    originalData = data;

    const sentences = data.sentences;
    const duration = data.metadata.duration;
    const youtube_video = data.metadata.input_video;
    const download_sub_directory = data.metadata.download_sub_directory;
    loadYoutubeVideo(youtube_video);
    const videoId = getYoutubeVideoID(youtube_video);

    sentences.forEach(item => {
        if (!tracks[item.speaker_index]) {
            tracks[item.speaker_index] = [];
        }
        tracks[item.speaker_index].push(item);
    });

    track_width = duration * pixelsPerSecond;
    edited_script_render_path = download_sub_directory + `\\` + loadedFileName;
    cliOutput.innerText = `turnvoice ` + videoId + ` --render "` + edited_script_render_path + `"`;

    // Create and draw blocks for each item on the appropriate track
    Object.keys(tracks).forEach(speakerIndex => {
        const track = document.createElement('div');
        track.classList.add('track');
        track.id = `track-${speakerIndex}`;
        track.style.width = `${track_width}px`;

        tracks[speakerIndex].forEach(item => {
            const block = document.createElement('div');
            block.classList.add('block', 'resize-drag');

            const duration = item.end - item.start;
            block.style.width = `${duration * pixelsPerSecond}px`;
            block.style.left = `${item.start * pixelsPerSecond}px`;
            block.oncontextmenu = function(event) {
                event.preventDefault();
                showContextMenu(event, block, speakerIndex);
            };
            block.dataset.text = item.text;
            block.dataset.fullSentence = item.full_sentence;
            block.textContent = item.text;  
            block.dataset.originalWidth = block.style.width;

            block.addEventListener('dblclick', function() {
                block.contentEditable = 'true';
                block.focus();
            });
            block.addEventListener('focus', function() {
                block.dataset.originalWidth = block.style.width;
                let originalWidth = parseInt(block.dataset.originalWidth, 10) || 0;
                block_width = Math.max(150, originalWidth);
                block.style.width = block_width + 'px';
                block.style.overflow = 'auto';
            }, true);
            block.addEventListener('blur', function() {
                block.style.width = block.dataset.originalWidth;
                block.style.overflow = 'hidden';
                block.contentEditable = 'false';
            }, true);
            block.addEventListener('input', function() {
                item.text = block.textContent.trim();
                block.dataset.text = item.text;
            });
            block.addEventListener('mouseenter', function() {
                block.style.zIndex = zIndexCounter++;
            });
            track.appendChild(block);
        });
        tracksContainer.appendChild(track);
    });

    updateCurrentTimeLineHeight();
}

function moveBlockToTrack(block, newSpeakerIndex) {

    let targetTrackId = `track-${newSpeakerIndex}`
    const targetTrack = document.getElementById(targetTrackId);

    if (targetTrack) {
        block.parentNode.removeChild(block);
        targetTrack.appendChild(block);

        block.oncontextmenu = function(event) {
            event.preventDefault();
            showContextMenu(event, block, newSpeakerIndex);
        };
    }
}

function showContextMenu(event, block, currentSpeakerIndex) {
    event.preventDefault();
    const existingMenu = document.querySelector('.context-menu');
    if (existingMenu) {
        existingMenu.remove();
    }
    const menu = document.createElement('ul');
    menu.classList.add('context-menu');
    menu.style.top = `${event.pageY}px`;
    menu.style.left = `${event.pageX}px`;

    // Add a menu item for deletion
    const deleteMenuItem = document.createElement('li');
    deleteMenuItem.innerText = 'Delete Clip';
    deleteMenuItem.onclick = () => deleteBlock(block, currentSpeakerIndex);
    menu.appendChild(deleteMenuItem);

    Object.keys(tracks).forEach(speakerIndex => {
        if (speakerIndex !== currentSpeakerIndex) {
            const menuItem = document.createElement('li');
            let speakerInt = parseInt(speakerIndex, 10);
            menuItem.innerText = `to Speaker ${speakerInt+1}`;
            menuItem.onclick = () => moveBlockToTrack(block, speakerIndex);
            menu.appendChild(menuItem);
        }
    });
    document.body.appendChild(menu);
    window.onclick = () => {
        menu.remove();
    };
}

function deleteBlock(block, speakerIndex) {
    // Remove the block from the DOM
    block.parentNode.removeChild(block);

    // Update the tracks data structure to remove the block data
    tracks[speakerIndex] = tracks[speakerIndex].filter(item => item.element !== block);
}

let player;

function getCurrentTime() {
    if (player && player.getCurrentTime) {
        return player.getCurrentTime();
    }
    return 0;
}

function onYouTubeIframeAPIReady() {
    player = new YT.Player('youtubePlayer', {
        height: '360',
        width: '640',
        videoId: '',
        events: {
            'onReady': onPlayerReady
        }
    });
}
function updateCurrentTimeLabel() {
    if (player && player.getCurrentTime) {
        const currentTime = player.getCurrentTime();
        const formattedTime = formatTime(currentTime);
        document.getElementById('currentTimeLabel').innerText = `🕒 ` + formattedTime;
    }
}

function formatTime(timeInSeconds) {
    const minutes = Math.floor(timeInSeconds / 60);
    const fullSeconds = Math.floor(timeInSeconds % 60);
    const hundredths = Math.floor((timeInSeconds % 1) * 100); 
    return `${pad(minutes)}:${pad(fullSeconds)}.${pad(hundredths, 2)}`;
}

function pad(number, length = 2) {
    let str = '' + number;
    while (str.length < length) {
        str = '0' + str;
    }
    return str;
}

function onPlayerReady(event) {
    createCurrentTimeLine();
    setInterval(updateCurrentTimeLabel, 20);
    setInterval(updateCurrentTimeLine, 20);
}

let currentTimeLine;

function updateCurrentTimeLineHeight() {
    let totalHeight = 0;
    const trackElements = document.querySelectorAll('.track');
    trackElements.forEach(track => {
        totalHeight += track.offsetHeight + 3;
    });

    if (currentTimeLine) {
        currentTimeLine.style.height = `${totalHeight}px`;
    }
}

function createCurrentTimeLine() {
    currentTimeLine = document.createElement('div');
    currentTimeLine.classList.add('current-time-line');
    timelineContainer.appendChild(currentTimeLine);
}

function updateCurrentTimeLine() {
    if (player && player.getCurrentTime && currentTimeLine) {
        const currentTime = player.getCurrentTime();
        const positionX = currentTime * pixelsPerSecond; 
        currentTimeLine.style.left = `${positionX}px`;
        timeline_position = positionX;
        if (autoScroll.checked && player.getPlayerState() === YT.PlayerState.PLAYING) {
            window.scrollTo(positionX - (document.documentElement.clientWidth / 2), 0);
        }  
    }
}

function isElementInViewport(el) {
    const rect = el.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

function getYoutubeVideoID(url) {
    const regExp = /^.*(youtu\.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*).*/;
    const match = url.match(regExp);

    if (match && match[2].length == 11) {
        return match[2];
    } else {
        alert('Invalid YouTube URL');
    }
}

function loadYoutubeVideo(url) {
    const videoId = getYoutubeVideoID(url);

    if (videoId && player) {
        player.loadVideoById(videoId);
    }
}

interact('.resize-drag')
    .resizable({
        edges: { left: true, right: true, bottom: false, top: false },
        listeners: {
            move (event) {
                var target = event.target;
                var x = (parseFloat(target.getAttribute('data-x')) || 0);
                target.style.width = event.rect.width + 'px';
                x += event.deltaRect.left;

                target.style.transform = 'translate(' + x + 'px)';

                target.setAttribute('data-x', x);
            }
        },
        modifiers: [
            interact.modifiers.restrictEdges({
                outer: 'parent'
            }),
        ]
    })
    .draggable({
        listeners: { move: window.dragMoveListener },
        modifiers: [
            interact.modifiers.restrictRect({
                restriction: 'parent',
                endOnly: true
            })
        ]
    });

function dragMoveListener(event) {
    var target = event.target;
    var x = (parseFloat(target.getAttribute('data-x')) || 0) + event.dx;
    target.style.transform = 'translate(' + x + 'px)';
    target.setAttribute('data-x', x);
}

function saveData() {
    let savedSentences = [];

    Object.keys(tracks).forEach(speakerIndex => {
        const track = document.getElementById(`track-${speakerIndex}`);
        const trackRect = track.getBoundingClientRect();

        const trackBlocks = document.querySelectorAll(`#track-${speakerIndex} .block`);
        
        trackBlocks.forEach(block => {
            const blockRect = block.getBoundingClientRect();
            const startPixels = blockRect.left - trackRect.left;
            const widthPixels = blockRect.width;
            const start = startPixels / pixelsPerSecond;
            const end = start + widthPixels / pixelsPerSecond;
            const text = block.dataset.text;
            const fullSentence = block.dataset.fullSentence;

            savedSentences.push({
                text: text, 
                start: start,
                end: end,
                full_sentence: fullSentence,
                speaker_index: speakerIndex,
            });
        });
    });

    const dataToSave = {
        metadata: originalData.metadata,
        sentences: savedSentences
    };

    downloadData(dataToSave);
}

function downloadData(data) {
    const prettyPrintedJson = JSON.stringify(data, null, 4);
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(prettyPrintedJson);
    const downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href", dataStr);
    const fileName = "downloaded_data.json";
    downloadAnchorNode.setAttribute("download", fileName);
    document.body.appendChild(downloadAnchorNode);
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
}

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('fileInput').addEventListener('change', handleFileSelect);
    document.getElementById('saveButton').addEventListener('click', saveData);
});
