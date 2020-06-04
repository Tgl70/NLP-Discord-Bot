
// require ibm-watson@^5.3.0

const urlTS = 'https://api.eu-gb.text-to-speech.watson.cloud.ibm.com/instances/2f102818-c2ce-4960-939f-a77cc5cea139';
const apiKeyTS = 'qiV1XROtRsRSXEoPo2za7_doLS19my_eOTak0QMMY1-w';

const fs = require('fs');
const TextToSpeechV1 = require('ibm-watson/text-to-speech/v1');
const { IamAuthenticator } = require('ibm-watson/auth');

const textToSpeechObj = new TextToSpeechV1({
  authenticator: new IamAuthenticator({
    apikey: apiKeyTS,
  }),
  url: urlTS,
});

text = "this is the fusion between jazz and funk ! it's junk ! and thats why you need to sort out the trash, to make the difference between jazz and funk";

function textToSpeech(text) {
    const synthesizeParams = {
	text: text,
	accept: 'audio/wav',
	voice: 'en-US_AllisonVoice',
    };

    return textToSpeechObj.synthesize(synthesizeParams);
}

// get the result
textToSpeech(text).then(audio => {
    // audio.result => stream with adio
    return audio.result.pipe(fs.createWriteStream('junk.wav'));
})
    .catch(err => {
	console.log('error:', err);
    });
