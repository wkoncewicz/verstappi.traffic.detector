// TODO: Rewrite to python 

const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(bodyParser.json());


async function initializeApp() {
    const PORT = 5000;
    app.listen(PORT, () => {
        console.log(`Server running on port ${PORT}`);
    });
}

initializeApp();

app.get('/message', async (req, res) => {
    res.status(200).json({ message:"naura" });
});
