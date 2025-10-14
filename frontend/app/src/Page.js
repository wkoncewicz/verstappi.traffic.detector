import { useState, useEffect } from 'react';
import axios from 'axios';
const url = "http://localhost:5000";

function Page() {
    const [message, setMessage] = useState("");

    useEffect(() => {
        const fetchData = async () => {
            try {
                const res = await axios.get(url + '/message');
                setMessage(res.data.message);
            } catch (error) {
                console.error('Error fetching posts:', error.message);
            }
        };
        fetchData();
    }, []);

    return (
        <div className="p-8 space-y-6 bg-gray-100">
            <h1>Welcome to our page!</h1>
            <div>This is a message from our backend: {message}</div>
        </div>
    );
}

export default Page;
