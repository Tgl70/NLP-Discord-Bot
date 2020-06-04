
// require ibm-watson@^5.3.0

const fs = require('fs');
const { IamAuthenticator } = require('ibm-watson/auth');
const SpeechToTextV1 = require('ibm-watson/speech-to-text/v1');

const speechToTextObj = new SpeechToTextV1({
  authenticator: new IamAuthenticator({
    apikey: 'sXcZ7gAbo54Nxp5MOOaSBQ9GVTMHB90LDBSJNiUsTn9M',
  }),
  url: 'https://api.eu-gb.speech-to-text.watson.cloud.ibm.com/instances/95c610ed-61dc-4f69-aff3-cc32936f0997',
});

function speechToText(stream, keywords) {

    var params = {
	objectMode: true,
	contentType: 'audio/wav',
	model: 'en-US_BroadbandModel',
	keywords: keywords,
	keywordsThreshold: 0.5,
	maxAlternatives: 3
    };

    var recognizeStream = speechToTextObj.recognizeUsingWebSocket(params);

    stream.pipe(recognizeStream);
    return recognizeStream;
}

// call de ma fc, retourne un stream de reponse du serv watson
recognizeStream = speechToText(fs.createReadStream('junk.wav'), ['jazz', 'funk']);

function onEvent(name, event) {
    console.log(name, JSON.stringify(event, null, 2));
};

// definition des "onevent" du stream pour watson
recognizeStream.on('data', function(event) { return onEvent('Data', event) });
recognizeStream.on('error', function(event) { onEvent('Error:', event); });
recognizeStream.on('error', function(event) { onEvent('Close:', event); });
