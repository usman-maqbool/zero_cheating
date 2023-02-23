// Scripts for firebase and firebase messaging
importScripts("https://www.gstatic.com/firebasejs/9.0.0/firebase-app-compat.js")
importScripts(
  "https://www.gstatic.com/firebasejs/9.0.0/firebase-messaging-compat.js"
)

const REACT_APP_APIKEY = "AIzaSyBiATXGicB11rMC96tjQuLoOwk-VtR4fRw"
const REACT_APP_AUTH_DOMAIN = "growtal-app.firebaseapp.com"
const REACT_APP_PROJECT_ID = "growtal-app"
const REACT_APP_STORAGE_BUCKET = "growtal-app.appspot.com"
const REACT_APP_MESSAGING_SENDER_ID = "412013044637"
const REACT_APP_APP_ID = "1:412013044637:web:b65052f8a83026f6da8574"
const REACT_APP_MEASUREMENT_ID = "G-MQ9Q765D4S"

const firebaseConfig = {
  apiKey: REACT_APP_APIKEY,
  authDomain: REACT_APP_AUTH_DOMAIN,
  projectId: REACT_APP_PROJECT_ID,
  storageBucket: REACT_APP_STORAGE_BUCKET,
  messagingSenderId: REACT_APP_MESSAGING_SENDER_ID,
  appId: REACT_APP_APP_ID,
  measurementId: REACT_APP_MEASUREMENT_ID
}

firebase.initializeApp(firebaseConfig)

// Retrieve firebase messaging
const messaging = firebase.messaging()

messaging.onBackgroundMessage(function (payload) {
  // console.log("Received background message ", payload)

  const notificationTitle = payload.notification.title
  const notificationOptions = {
    body: payload.notification.body
  }
  self.registration.showNotification(notificationTitle, notificationOptions)
})

messaging.onMessage(payload => {
  // console.log("===========>>>>>>>", payload)
})

// messaging.onMessage(function (payload) {
//   console.log("Received forground message ", payload)

//   const notificationTitle = payload.notification.title
//   const notificationOptions = {
//     body: payload.notification.body
//   }
//   self.registration.showNotification(notificationTitle, notificationOptions)
// })

// if ("serviceWorker" in navigator) {
//   navigator.serviceWorker
//     .register("../firebase-messaging-sw.js")
//     .then(function (registration) {
//       console.log("Registration successful, scope is:", registration.scope)
//     })
//     .catch(function (err) {
//       console.log("Service worker registration failed, error:", err)
//     })
// }
