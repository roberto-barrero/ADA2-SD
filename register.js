// A function to send a SOAP request to a web service
// and return the response
function sendSoapRequest(url, soapAction, soapBody) {
  var request = new XMLHttpRequest();
  request.open("POST", url, false);
  request.setRequestHeader("Content-Type", "text/plain");
  request.send(soapBody);
  return request.responseXML;
}

// add and event listener to the submit button
document.getElementById("form").addEventListener("submit", (e) => {
  // get the username and password from the form
  e.preventDefault();
  console.log("Peticion enviada");
  let username = document.getElementById("username").value;
  let password = document.getElementById("password").value;
  let name = document.getElementById("name").value;
  let email = document.getElementById("email").value;

  let url = "http://localhost:5000/createUser";

  let soapAction = "http://localhost:5000/createUser";

  let soapBody = `<?xml version="1.0" encoding="UTF-8"?>
  <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:user="http://localhost:5000/user-service">
    <soap:Header/>
    <soap:Body>
      <user:createUserRequest>
        <user:user>
          <user:username>${username}</user:username>
          <user:password>${password}</user:password>
          <user:email>${email}</user:email>
          <user:name>${name}</user:name>
        </user:user>
      </user:createUserRequest>
    </soap:Body>
  </soap:Envelope>`;

  response = sendSoapRequest(url, soapAction, soapBody);
  console.log(response);

  if (response) {
    
    alert("Usuario creado");
    window.location.href = "./login.html";
  }
});
