// A function to send a SOAP request to a web service
// and return the response
function sendSoapRequest(url, soapAction, soapBody) {
  var request = new XMLHttpRequest();
  request.open("POST", url, false);
  request.setRequestHeader("Content-Type", "text/plain");
  request.send(soapBody);
  return request.responseXML;
}
let username = "johndoe";
let password = "mysecretpassword";

// add and event listener to the submit button
document.getElementById("form").addEventListener("submit", (e) => {
  // get the username and password from the form
  e.preventDefault();
  console.log("Peticion enviada");
  username = document.getElementById("username").value;
  password = document.getElementById("password").value;

  let url = "http://localhost:8000/authentication";

  let soapAction = "http://localhost:8000/authentication";

  let soapBody = `<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:aut="http://localhost:8000/authentication">
  <soapenv:Header/>
  <soapenv:Body>
    <aut:login>
        <aut:username>${username}</aut:username>
        <aut:password>${password}</aut:password>
    </aut:login>
  </soapenv:Body>
  </soapenv:Envelope>`;

  console.log(soapBody);

  response = sendSoapRequest(url, soapAction, soapBody);
  console.log(response);

  // Pasre the reponse that is a XML document and get the authToken element inside the response LoginReponse element
  let authToken = response
    .getElementsByTagName("ns1:LoginResponse")[0]
    .getElementsByTagName("ns1:authToken")[0].innerHTML;

  // Store the authToken in the local storage
  localStorage.setItem("username", username);
  localStorage.setItem("authToken", authToken);
});
