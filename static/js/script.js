document.addEventListener("DOMContentLoaded", () => {
    const quizForm = document.querySelector("form[data-quiz]");
    if (quizForm) {
        quizForm.addEventListener("submit", (e) => {
            e.preventDefault();
            let score = 0;
            const questions = quizForm.querySelectorAll("div.question");
            questions.forEach(q => {
                const selected = q.querySelector("input[type='radio']:checked");
                if (selected && selected.value === q.dataset.answer) {
                    score += 10;
                    q.style.backgroundColor = "#d4edda"; // green
                } else {
                    q.style.backgroundColor = "#f8d7da"; // red
                }
            });
            alert(`You scored ${score} points!`);
            window.location.href = "/dashboard";
        });
    }
});
