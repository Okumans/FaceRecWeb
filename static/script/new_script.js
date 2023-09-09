const blobToBase64 = blob => {
    const reader = new FileReader();
    reader.readAsDataURL(blob);
    return new Promise(resolve => {
    reader.onloadend = () => {
        resolve(reader.result);
    };
    });
};

function imageToBase64(imageData) {
    return new Promise(resolve => {
        const canvas = document.createElement('canvas');
        canvas.width = imageData.width;
        canvas.height = imageData.height;
        const context = canvas.getContext('2d');
        context.putImageData(imageData, 0, 0);
        canvas.toBlob(blob => {
            const reader = new FileReader();
            reader.onload = () => {
                resolve(reader.result);
            };
            reader.readAsDataURL(blob);
        }, 'image/png');
    });
}

function validate(){
    var needToFill = []
    if (realName.value === "") needToFill.push("name")
    if (nickname.value === "") needToFill.push("nickname")
    if (studentId.value === "") needToFill.push("student number")
    if (studentClass.value === "") needToFill.push("class")
    if (classNumber.value === "") needToFill.push("number")

    if (needToFill.length > 1) alert(`Please fill in ${needToFill.slice(0, -1).join(", ")} and ${needToFill.slice(-1)}`)
    else if (needToFill.length == 1) alert(`Please fill in ${needToFill[0]}`)
    else return true
    return false
}

function realname_separator(realname){
    realname = realname.trim()
    var parts = realname.split(" ")
    if (parts.length == 1){
        return [parts[0], ""]
    }
    else if (parts.length > 1){
        return [parts.slice(0, -1).join(" "), parts.slice(-1).join("")]
    }
    else{
        return ["", ""]
    }

}

const camera = document.getElementById('camera')
const cameraCanvas = document.getElementById('canvas')
const uploadInput = document.getElementById('upload-input')
const captureInput = document.getElementById('capture-input')
const video = document.getElementById('video');
const preview = document.getElementById('preview');
const recordButton = document.getElementById('record');
const stopButton = document.getElementById('stop');
const uploadForm = document.getElementById('upload-form')
const captureForm = document.getElementById('capture-form')
const submitButton = document.getElementById('submit-button')
const frameCounter = document.getElementById('frame-count')
const maxFrameNumber = 80

const realName = document.getElementById("name")
const nickname = document.getElementById("nickname")
const studentId = document.getElementById("student-id")
const studentClass = document.getElementById("student-class")
const classNumber = document.getElementById("class-number")

var mediaRecorder;
var chunks = [];
var mode = 0; // mode 0 is camera, mode 1 is file
var images = []
var profileImage = ""

stopButton.disabled = true;
document.getElementById("camera-buttons").style.height = video.height+"px"
document.getElementById("images-grid").style.display = "none"

Promise.all([
    faceapi.nets.tinyFaceDetector.loadFromUri('/static/script/models'),
    faceapi.nets.faceLandmark68Net.loadFromUri('/static/script/models'),
    faceapi.nets.faceRecognitionNet.loadFromUri('/static/script/models')
]).then(startVideo)

function startVideo(){
    navigator.mediaDevices.getUserMedia({ video: {} })
        .then(function (stream) {
        video.srcObject = stream;
        video.play();
        mediaRecorder = new MediaRecorder(stream);

        mediaRecorder.ondataavailable = function (e) {
            chunks.push(e.data);
        };
        
        mediaRecorder.onstop = async function () {
            var blob = new Blob(chunks, { type: 'video/mp4' });
            var videoURL = URL.createObjectURL(blob);
            var videoB64 = await blobToBase64(blob);
    
            captureInput.value = videoB64;
            preview.src = videoURL;
            preview.style.display = 'block';
            uploadInput.value = '';
        };
        })
    
        .catch(function (err) {
        console.error('Could not access camera:', err)
        });
}
//#a14a60
video.addEventListener('playing', function() {
    const canvas = faceapi.createCanvasFromMedia(video)
    const context = canvas.getContext('2d')
    const displaySize = {width: video.width,
                         height: video.height}
    var cleared = false;
    canvas.style.position = "absolute"
    canvas.style.marginLeft = "20px";
    canvas.style.marginTop= "0px";

    document.getElementById("preview").append(canvas, video)
    faceapi.matchDimensions(canvas, displaySize)
    
    setInterval(async function(){
        frameCounter.innerHTML = `${images.length}/${maxFrameNumber}`
        if (images.length >= maxFrameNumber){
            stopButton.click()
        }

        if (recordButton.disabled){
            cleared = false;
            const detections = await faceapi.detectAllFaces(video,
                new faceapi.TinyFaceDetectorOptions())
                .withFaceLandmarks()
            const resizeDetections = faceapi.resizeResults(detections, displaySize)
            
            context.drawImage(video, 0, 0, canvas.width, canvas.height)
            context.clearRect(0, 0, canvas.width, canvas.height)

            // console.log(!!detections, detections.length)
            if (detections.length){
                const detection = resizeDetections[0].detection
                const croppedCanvas = document.createElement('canvas')
                croppedCanvas.width = detection._box._width
                croppedCanvas.height = detection._box._height+40
                const croppedContext = croppedCanvas.getContext('2d')
                croppedContext.drawImage(video, detection._box._x+60, detection._box._y, 
                    detection._box._width, detection._box._height+40, 0, 0, detection._box._width,
                    detection._box._height+40);
                const imageData = croppedCanvas.toDataURL('image/png');
                images.push(imageData)
            }

            console.log('info', images)
            faceapi.draw.drawDetections(canvas, resizeDetections)
            faceapi.draw.drawFaceLandmarks(canvas, resizeDetections)
        }
        else{
            if (cleared == false){
                context.clearRect(0, 0, canvas.width, canvas.height)
                cleared = true;
            }
        }
    }, 100)
})

recordButton.addEventListener('click', function () {
    mode = 0; // set mode to camera
    mediaRecorder.start();

    recordButton.disabled = true;
    stopButton.disabled = false;
    images = []
});

stopButton.addEventListener('click', function () {
    mediaRecorder.stop();
    recordButton.disabled = false;
    stopButton.disabled = true;
    submitButton.disabled = false;
    for (const imageIndex in images){
        const imageUrl = images[imageIndex]
        var image = new Image()
        image.src = imageUrl;
        document.getElementById("images-grid").appendChild(image)
    }
    // document.getElementById("images-grid").style.display = "grid"
});

uploadForm.addEventListener('change', function () {
    mode = 1; // change mode to file
    submitButton.disabled = false;
    preview.src = URL.createObjectURL(uploadInput.files[0]);

});

submitButton.addEventListener('click', function () {
    if (!validate()) return false
    
    if (mode == 1) { // if is file mode
    var formData = new FormData(uploadForm);
    formData.append("profile", profileImage)
    formData.append("PersonalInformation", JSON.stringify({
        realname: realname_separator(realName.value)[0],
        surname: realname_separator(realName.value)[1],
        nickname: nickname.value.trim(),
        student_id: studentId.value.trim(),
        student_class: studentClass.value.trim(),
        class_number: classNumber.value.trim()
    }))

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
        .then(response => response.text())
        .then(response => {
            // handle the successful response from the server
            console.log("Image uploaded successfully! ID: " + response);
            alert(`your queue id is ${response}`)
            window.location.replace(window.location.origin+"/queues/"+response)
        })
        .catch(function (error) {
        console.error('Error uploading video :(')
        })
    }
    else {
    const data = JSON.stringify({
        images: images,
        profile: profileImage,
        PersonalInformation:{
            realname: realname_separator(realName.value)[0],
            surname: realname_separator(realName.value)[1],
            nickname: nickname.value.trim(),
            student_id: studentId.value.trim(),
            student_class: studentClass.value.trim(),
            class_number: classNumber.value.trim()
        }
    })

    fetch('/capture', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: data
    })
        .then(response => response.text())
        .then(response => {
            // handle the successful response from the server
            console.log("Image uploaded successfully! ID: " + response);
            alert(`your queue id is ${response}`)
            window.location.replace(window.location.origin+"/queues/"+response)
        })
        .catch(function (error) {
        console.error('Error uploading video :(')
        })
    }
    submitButton.disabled = true;
    uploadForm.reset();

})

const uploadImageInput = document.getElementById('upload-image-form');

// listen for change event on the file input element
uploadImageInput.addEventListener('change', (event) => {
  const file = event.target.files[0]

  // create a FileReader object to read the file
  const reader = new FileReader()

  // listen for load event on the FileReader object
  reader.addEventListener('load', () => {
    // create an image element and set its source to the loaded data URL
    const image = document.getElementById("preview-profile")
    image.src = reader.result
    profileImage = reader.result
  });

  // read the file as a data URL
  reader.readAsDataURL(file)
});

