document.addEventListener('DOMContentLoaded', () => {
    const cards = document.querySelectorAll('.catalog-card');
    const body  = document.getElementById('detailBody');
    const empty = document.getElementById('detailEmpty');
    const img   = document.getElementById('detailImg');
    const title = document.getElementById('detailTitle');
    const price = document.getElementById('detailPrice');
    const desc  = document.getElementById('detailDesc');
    const placeholder = "{{ url_for('static', filename='img/placeholder-car.jpg') }}";

    cards.forEach(card => {
        card.addEventListener('click', () => {
            document.querySelectorAll('.catalog-card.active').forEach(c => c.classList.remove('active'));
            card.classList.add('active');

            const make  = card.dataset.make;
            const model = card.dataset.model;
            const year  = card.dataset.year;
            const p     = card.dataset.price;
            const d     = card.dataset.description;
            const src   = card.dataset.img;

            title.textContent = `${year} ${make} ${model}`;
            price.textContent = `$${p}`;
            desc.textContent = d;

            empty.classList.add('d-none');
            body.classList.remove('d-none');
        });
    });
});
