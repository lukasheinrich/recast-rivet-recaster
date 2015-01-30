# recast-rivet-recaster

steps

    virtualenv --system-site-packages venv
    source venv/bin/activate
    git clone git@github.com:lukasheinrich/recast-rivet-recaster-demo.git
    cd recast-rivet-recaster-demo/
    pip install -e . --process-dependency-links
    cd implementation
    celery worker -A recastrivet.general_rivet_backendtasks -l debug -Q rivet_queue
