const baseURL = "http://localhost:5000";

window.onload = () => {
    console.log("Scripts loaded.");
    displayChatrooms();
    displayMessages();

    // Poll for new messagess
    setInterval(() => {
        displayNewMessages();
    }, 1000);

    if (document.getElementById("send-new-message"))
        document.getElementById("send-new-message")
            .onclick = () => sendMessage();

    if (document.getElementById("message-input")) {
        const msgEle = document.getElementById("message-input");
        msgEle.onkeypress = e => checkForEnter(e);
        msgEle.focus();
    }
}

function checkForEnter (e) {
    if (e.key === "Enter")
        sendMessage();
}

async function sendMessage() {
    let msgEle = document.getElementById("message-input");
    const msgVal = msgEle.value.trim();
    if (msgVal.length > 256) {
        alert("Message is too long!");
        return;
    }
    if (msgVal.length === 0) return;

    msgEle.focus();
    msgEle.value = "";
    
    console.log("Sending message.");
    const res = await fetch(`${baseURL}/send_message`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message: msgVal })
    })

    console.log(`Status: ${res.statusText}`);

    if (res.redirected) {
        alert("Chatroom was deleted by owner");
        window.location.assign(res.url);
    }
}

async function displayChatrooms() {
    let ele = document.getElementById('rooms-list');
    if (!ele) return;
    console.log("Displaying rooms.");
    
    const rooms = await getChatrooms();
    const uid = (await getUser()).uid;
    
    for (let room of rooms) {
        let child = document.createElement("div");
        child.classList.add("card", "chat-preview", "flex-col");

        // Room title
        let h1 = document.createElement("h1");
            h1.classList.add("preview-title");
            h1.textContent = room.name;

        // Join link
        let a = document.createElement("a");
            a.href = `/join/id=${room.id}name=${room.name}`;
            a.textContent = "Join";

        // Delete button for owner only
        let del;
        if (room.owner == uid) {
            del = document.createElement("p");
            del.textContent = "Delete";
            del.classList.add("delete-chat");
            console.log(`${baseURL}/delete_chat/${room.id}`)
            del.onclick = () => {
                fetch(`${baseURL}/delete_chat/${room.id}`,
                { method: "DELETE", headers: { "Origin": `${baseURL}/delete_chat/${room.id}`} } )
                .then(res => console.log("Room deleted."))
                .catch(err => console.error(err))
                .then(() => window.location.reload())
            }
        }

        del ? child.append( h1, a, del )
            : child.append( h1, a );

        ele.append(child);
    }

    if (rooms.length === 0){
        let hint = document.createElement("div");
        hint.textContent = "No chatrooms available currently.";
        hint.style.textAlign = "center";
        ele.append(hint);
    }
}

async function displayMessages() {
    if (!document.getElementById("messages")) return;
    const messages = await getMessages();
    renderMessagesFromList(messages);
}

async function displayNewMessages() {
    if (!document.getElementById("messages")) return;
    const messages = await getNewMessages();   
    renderMessagesFromList(messages);
}

async function renderMessagesFromList (messages) {
    let ele = document.getElementById("messages");
    const uname = (await getUser()).username;

    for (let message of messages) {
        let child = document.createElement("div");
        child.classList.add("message");
        message.sender === uname &&  child.classList.add("my-message");

        let p1 = document.createElement("p");;
            p1.classList.add("message-sender");
            p1.textContent = message.sender + ":";

        let p2 = document.createElement("p");;
            p2.classList.add("message-content");
            p2.textContent = message.content;

        child.append( p1, p2 );

        ele.append(child);
    }

    ele.scrollTo({ top: ele.scrollHeight });
}

async function getMessages () {
    let res = await (await fetch(`${baseURL}/get_messages`)).json();
    return res.messages;
}

async function getNewMessages () {
    let res = await (await fetch(`${baseURL}/get_new_messages`)).json();
    return res.messages;
}

async function getChatrooms () {
    let res = await (await fetch(`${baseURL}/get_chats`)).json();
    return res.rooms;
}

async function getUser () {
    let res = await (await fetch(`${baseURL}/get_user`)).json();
    return res;
}